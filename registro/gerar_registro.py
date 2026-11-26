# Monta o REGISTRO_GERAL.md (raiz do repositório): a parte escrita à mão (registro/REGISTRO_MANUAL.md) + um apêndice
# refeito sozinho com a situação das rotinas, o resultado de cada validação e a lista de todas as mudanças do
# repositório. A fila da conferência chama este script depois de cada tarefa. Não fala com o Earth Engine.
#     python registro/gerar_registro.py
import glob
import os
import subprocess
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRT = timezone(timedelta(hours=-3))
RESULTADOS = [
    ('Conferência final (fila)', 'rotinas/conferencia/CONFERENCIA_FINAL.md'),
    ('2026 × CHIRPS e MODIS', 'pesquisa/resultados_2026/RESULTADOS.md'),
    ('Solo, folha e ET real × SMAP e MODIS', 'pesquisa/resultados_solo_folha/RESULTADOS.md'),
    ('Escoamento × CAMELS-BR', 'pesquisa/resultados_escoamento/RESULTADOS.md'),
    ('Método de 2026 em 2021–2025', 'pesquisa/resultados_metodo_2026/RESULTADOS_A.md'),
    ('2026 × GLDAS-2.1', 'pesquisa/resultados_metodo_2026/RESULTADOS_B.md'),
    ('Histórico por década × TerraClimate e CHIRPS', 'pesquisa/resultados_historico/RESULTADOS.md'),
    ('Tudo por mês do ano', 'pesquisa/RESULTADOS_POR_MES.md'),
    ('Sensibilidade à resolução', 'pesquisa/resultados_resolucao/RESULTADOS.md'),
    ('Correção dos dias ERA5 (fase 1)', 'pesquisa/resultados_correcao_era5/RESULTADOS.md'),
    ('Fase 2, M1-C3R', 'pesquisa/resultados_fase2/RESULTADOS_M1_C3R.md'),
    ('Fase 2, leva 1', 'pesquisa/resultados_fase2/RESULTADOS_LEVA1.md'),
    ('Fase 2, leva 2', 'pesquisa/resultados_fase2/RESULTADOS_LEVA2.md'),
    ('Várias referências (multifonte)', 'pesquisa/resultados_multifonte/RESULTADOS.md'),
    ('BR-DWGD: artigos, site e relatório', 'pesquisa/resultados_brdwgd/ANALISE_DOS_ARTIGOS.md'),
    ('BR-DWGD bruto ano a ano', 'pesquisa/resultados_brdwgd/RESULTADOS.md'),
    ('Previsão estendida (pesquisa)', 'pesquisa/resultados/RESULTADOS.md'),
    ('Acerto da previsão GFS', 'rotinas/resultados/previsao/ACERTO.md'),
]


def ler(rel):
    p = os.path.join(RAIZ, rel)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else None


def main():
    L = [ler('registro/REGISTRO_MANUAL.md').rstrip(), '', '---', '',
         f'# Apêndice automático (refeito em {datetime.now(BRT):%d/%m/%Y %H:%M}, Brasília)', '']
    painel = ler('rotinas/PAINEL.md')
    if painel:
        tab = [x for x in painel.splitlines() if x.startswith('|')]
        L += ['## A. Situação das rotinas automáticas (de `rotinas/PAINEL.md`)', '', *tab, '']
    L += ['## B. Resultado de cada validação', '',
          'Cada bloco é a cópia do arquivo de resultado no momento em que este registro foi refeito.', '']
    for nome, rel in RESULTADOS:
        txt = ler(rel)
        L += [f'### {nome}', '', f'Arquivo: `{rel}`', '']
        if not txt:
            L += ['(ainda não rodou)', '']
            continue
        if rel.endswith('CONFERENCIA_FINAL.md') or rel.endswith('POR_MES.md'):
            txt = txt.split('\n---\n')[0]          # só a tabela da fila; os blocos estão logo abaixo
            if rel.endswith('POR_MES.md'):
                txt = '(arquivo longo: abra o arquivo)'
        L += [x.replace('# ', '#### ', 1) if x.startswith('#') else x for x in txt.strip().splitlines()] + ['']
    log = subprocess.run(['git', 'log', '--date=format:%d/%m/%Y %H:%M', '--format=| %ad | %s |'], cwd=RAIZ,
                         capture_output=True, text=True).stdout.strip().splitlines()
    L += ['## C. Todas as mudanças do repositório `sab-pedidos` (da mais nova para a mais antiga)', '',
          'As do `sab-motor` ficam no GitHub dele (Commits); as anteriores ao GitHub, nos changelogs da entrega.', '',
          '| Quando | Mudança |', '|---|---|', *[x.replace('[skip ci]', '').strip() for x in log], '']
    with open(os.path.join(RAIZ, 'REGISTRO_GERAL.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'REGISTRO_GERAL.md: {len(L)} linhas')


if __name__ == '__main__':
    main()
