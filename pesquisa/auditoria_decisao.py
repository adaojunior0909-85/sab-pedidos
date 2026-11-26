# Seção 4 do protocolo da auditoria profunda: a decisão por variável × região, a partir do A1 (persistência), do A2
# (El Niño / La Niña) e do A3 (água, só na chuva). Sem Earth Engine; refeita sempre que um teste é atualizado.
#     python pesquisa/auditoria_decisao.py
import os

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(AQUI, 'resultados_auditoria')
NOME = {'pr_mm': 'Chuva', 'tmax_C': 'Tmax', 'tmin_C': 'Tmin', 'rs': 'Radiação', 'RH': 'Umidade relativa', 'u2': 'Vento',
        'et_potencial': 'ETo', 'vpd': 'VPD'}


def main():
    p = pd.read_csv(os.path.join(AUD, 'A1_persistencia.csv'))
    v = pd.read_csv(os.path.join(AUD, 'A2_veredito.csv'))
    a3f = os.path.join(AQUI, 'resultados_agua', 'A3_veredito.csv')
    a3 = pd.read_csv(a3f) if os.path.exists(a3f) else pd.DataFrame(columns=['testemunha', 'regiao', 'veredito'])
    d = p.merge(v, on=['regiao', 'variavel'], how='outer')
    linhas = []
    for r in d.itertuples():
        pers = bool(r.persistente) if pd.notna(r.persistente) else False
        a2 = r.veredito_A2 if pd.notna(r.veredito_A2) else 'inconclusivo'
        fis = a3[a3.regiao == r.regiao].veredito.tolist() if r.variavel == 'pr_mm' else []
        com_ref, com_sab = fis.count('com as referências'), fis.count('com o SAB')
        if r.variavel == 'pr_mm':
            a3txt = ', '.join(f'{t}: {x}' for t, x in zip(a3[a3.regiao == r.regiao].testemunha, fis)) or 'sem dado'
        else:
            a3txt = '(não se aplica)'
        if a2 == 'explica' or (r.variavel == 'pr_mm' and com_sab > 0):
            dec = 'clima (nenhuma correção)'
        elif pers and a2 == 'não explica' and (r.variavel != 'pr_mm' or (com_ref >= 1 and com_sab == 0)):
            dec = '**DEGRAU DOS DADOS CONFIRMADO**'
        elif not pers:
            dec = 'sem degrau persistente'
        else:
            dec = 'inconclusivo → aviso no dicionário'
        linhas.append({'variavel': r.variavel, 'regiao': r.regiao, 'A1_persistente': pers,
                       'A1_anos': r.anos_confirmados, 'A2': a2, 'A3': a3txt, 'decisao': dec})
    t = pd.DataFrame(linhas)
    t.to_csv(os.path.join(AUD, 'DECISAO.csv'), index=False)
    L = ['# Auditoria profunda: decisão (seção 4 do protocolo)', '',
         'Regras fixadas antes de rodar (`pesquisa/PROTOCOLO_AUDITORIA_PROFUNDA.md`, seção 4): **degrau dos dados '
         'confirmado** = A1 persistente + A2 "não explica" + (na chuva) A3 com ≥ 1 testemunha física com as referências e '
         'nenhuma com o SAB; **clima** = A2 "explica" ou (na chuva) testemunha física com o SAB; senão **inconclusivo** '
         '(aviso no dicionário, nenhuma correção). Só as linhas com degrau persistente ou decisão diferente de "sem '
         'degrau" aparecem abaixo; a tabela inteira está em `DECISAO.csv`.', '',
         '| Variável | Região | A1 (anos 2020–24) | A2 | A3 (água) | Decisão |', '|---|---|---|---|---|---|']
    for r in t.sort_values(['variavel', 'regiao']).itertuples():
        if r.decisao == 'sem degrau persistente' and r.A2 != 'explica':
            continue
        L.append(f'| {NOME.get(r.variavel, r.variavel)} | {r.regiao} | '
                 f'{"-" if pd.isna(r.A1_anos) else int(r.A1_anos)}{" (persistente)" if r.A1_persistente else ""} | '
                 f'{r.A2} | {r.A3} | {r.decisao} |')
    L.append('')
    with open(os.path.join(AUD, 'DECISAO.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
