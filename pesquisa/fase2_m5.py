# Fase 2, M5 (pesquisa/PROTOCOLO_CORRECAO_FASE2.md, M5 + emenda 1): o teste do ajuste dos degraus CONFIRMADOS do
# histórico (≥ 2 referências independentes no validar_multifonte.py). Sem Earth Engine; só leitura; nada é gravado.
# Método do protocolo: o nível da década suspeita vai para a relação média com a referência nas décadas vizinhas
# (aditivo nas temperaturas, UR e VPD; multiplicativo na chuva, vento, radiação e nas somas). Regra do protocolo:
# depois do ajuste, a década deixa de ser suspeita nas referências que a marcaram e nenhuma outra década passa a ser.
# Detalhes de implementação (o texto do M5 não fixava; escritos antes de rodar, 26/11/2026 ~13h30):
#   - décadas vizinhas = a anterior e a seguinte que existirem com dado naquela referência;
#   - com mais de uma referência confirmando, o ajuste é a média dos ajustes de cada uma;
#   - "nenhuma outra década passa a ser" é conferido em TODAS as fontes daquela variável e região;
#   - as variáveis do modelo (ET real, escoamento, transpiração, solo, folha) entram só como relato: o M4 fixou que elas
#     não recebem correção.
#     python pesquisa/fase2_m5.py
import os
import sys

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import validar_multifonte as mf  # noqa: E402

SAIDA = os.path.join(AQUI, 'resultados_fase2')
MULT = mf.SOMA | {'rs', 'u2'}
MODELO = {'et_real', 'runoff', 'transpiracao_mm', 'tsolo_C', 'tfolha_C', 'soil_moisture_0_5cm_m3_m3',
          'soil_moisture_0_100cm_m3_m3', 'runoff_sup_mm', 'runoff_sub_mm'}


def relacao(g, var, a, z):
    x = g[g.ano.between(a, z)].dropna(subset=['sab', 'referencia'])
    if len(x) < 24:
        return None
    return x.sab.sum() / x.referencia.sum() if var in MULT else (x.sab - x.referencia).mean()


def marcas(df, var, reg):
    out = {}
    for f, g in df[(df.variavel == var) & (df.regiao == reg)].groupby('fonte'):
        g = g.copy()
        for k in ('sab', 'referencia'):
            g[f'a_{k}'] = g[k] - g.groupby('mes')[k].transform('mean')
        out[f] = {d for d, v in mf.degraus(mf.decadas(g, var), var).items() if v}
    return out


def main():
    df = mf.carregar()
    conf = []
    for (fonte, var, reg), g in df.groupby(['fonte', 'variavel', 'regiao']):
        if reg not in mf.REGIOES:
            continue
        for d, v in mf.degraus(mf.decadas(g, var), var).items():
            if v:
                conf.append((var, reg, d, fonte))
    c = pd.DataFrame(conf, columns=['variavel', 'regiao', 'decada', 'fonte'])
    linhas = []
    for (var, reg, d), g in c.groupby(['variavel', 'regiao', 'decada']):
        n, grupos = mf.conta_independente(list(g.fonte), var)
        if n < 2:
            continue
        refs = list(g.fonte)
        ajustes = []
        for f in refs:
            s = df[(df.variavel == var) & (df.regiao == reg) & (df.fonte == f)]
            alvo = [relacao(s, var, a, z) for (a, z) in mf.DECADAS
                    if abs(mf.DECADAS.index((a, z)) - mf.DECADAS.index(d)) == 1]
            alvo = [x for x in alvo if x is not None]
            atual = relacao(s, var, *d)
            if not alvo or atual is None or (var in MULT and atual == 0):
                continue
            m = sum(alvo) / len(alvo)
            ajustes.append(m / atual if var in MULT else m - atual)
        if not ajustes:
            linhas.append({'variavel': var, 'regiao': reg, 'decada': f'{d[0]}-{d[1]}', 'referencias': ', '.join(grupos),
                           'ajuste': None, 'some_nas_refs': None, 'novas_decadas': None, 'passa': False,
                           'nota': 'sem década vizinha com dado'})
            continue
        aj = sum(ajustes) / len(ajustes)
        antes = marcas(df, var, reg)
        df2 = df.copy()
        sel = (df2.variavel == var) & (df2.regiao == reg) & df2.ano.between(*d)
        df2.loc[sel, 'sab'] = df2.loc[sel, 'sab'] * aj if var in MULT else df2.loc[sel, 'sab'] + aj
        depois = marcas(df2, var, reg)
        some = all(d not in depois.get(f, set()) for f in refs)
        novas = sorted({f'{x[0]}-{x[1]} ({f})' for f in depois for x in depois[f] - antes.get(f, set()) if x != d})
        passa = some and not novas
        linhas.append({'variavel': var, 'regiao': reg, 'decada': f'{d[0]}-{d[1]}', 'referencias': ', '.join(grupos),
                       'ajuste': aj, 'some_nas_refs': some, 'novas_decadas': '; '.join(novas), 'passa': passa,
                       'nota': 'variável do modelo: só relato (M4)' if var in MODELO else ''})
    t = pd.DataFrame(linhas)
    os.makedirs(SAIDA, exist_ok=True)
    t.to_csv(os.path.join(SAIDA, 'M5_ajustes.csv'), index=False)
    L = ['# Fase 2, M5: ajuste dos degraus confirmados do histórico (teste, só leitura)', '',
         'Protocolo `pesquisa/PROTOCOLO_CORRECAO_FASE2.md` (M5 e emenda 1). Detalhes de implementação no cabeçalho de '
         '`pesquisa/fase2_m5.py`. Ajuste: × fator (chuva, vento, radiação, somas) ou + diferença (temperaturas, UR, VPD). '
         '**Passa** = a década deixa de ser suspeita nas referências que a marcaram e nenhuma outra década passa a ser, '
         'em nenhuma fonte. Nada é gravado: o que passa vai ao responsável (correção só na leitura, com K16).', '',
         '| Variável | Região | Década | Referências | Ajuste | Some nas refs? | Novas décadas suspeitas | Passa? | Nota |',
         '|---|---|---|---|---|---|---|---|---|']
    for r in t.itertuples():
        aj = '-' if pd.isna(r.ajuste) else (f'× {r.ajuste:.3f}' if r.variavel in MULT else f'{r.ajuste:+.3f}')
        L.append(f'| {mf.NOME.get(r.variavel, r.variavel)} | {r.regiao} | {r.decada} | {r.referencias} | {aj} | '
                 f'{"-" if r.some_nas_refs is None else ("sim" if r.some_nas_refs else "não")} | {r.novas_decadas or "-"} | '
                 f'{"✅" if r.passa else "❌"} | {r.nota} |')
    pas = t[t.passa & ~t.variavel.isin(MODELO)]
    L += ['', f'**Passaram (variáveis do BR-DWGD): {len(pas)} de {int((~t.variavel.isin(MODELO)).sum())}.** '
          + ('; '.join(f'{mf.NOME.get(r.variavel, r.variavel)} {r.regiao} {r.decada}' for r in pas.itertuples()) or '')]
    with open(os.path.join(SAIDA, 'RESULTADOS_M5.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
