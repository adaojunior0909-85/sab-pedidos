# Verificação COM Earth Engine da correção 2026.11.18 (pedido de uma variável só saía com a coluna vazia).
# Não exporta nada: só lê o SAB_V1 com getInfo, num pixel de Cascavel-PR, e imprime o resultado.
# Rodar: no GitHub Actions (workflow "Verificar correcao uma variavel") ou no Colab, na pasta do repositório:
#     python testes/verificar_uma_variavel_ee.py
#
# O que confere, para CADA uma das 19 variáveis pedida SOZINHA (diário e mensal):
#   - ANTIGO: o redutor de antes (ee.Reducer.mean() sem nome) -> esperado: coluna vazia (bug);
#   - NOVO:   o redutor corrigido (_redutor_media)            -> esperado: o mesmo valor do pedido "todas".
# O pedido "todas" (19 variáveis juntas) é a referência: com várias bandas o Earth Engine sempre deu o nome certo,
# e a correção não mexe nesse caso (K16 igual).
import os
import sys
from datetime import date, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import ee  # noqa: E402
import sab_pedido as sp  # noqa: E402

LAT, LON = sp.centro_do_pixel(-25.34953, -53.45031)   # um pixel de Cascavel-PR (o da planilha)
DIA_HISTORICO = '2025-11-17'                            # Historico_Observado (BR-DWGD)
MESES = (('2025-11-01', '2025-12-01', 2025), ('2026-10-01', '2026-11-01', 2026))

ee.Initialize(project=sp.PROJETO)
_novo = sp._redutor_media


def _antigo(bandas):
    return ee.Reducer.mean()


geom = ee.Geometry.Point([LON, LAT])
grade = ee.FeatureCollection([ee.Feature(geom, {
    'Nome_Local_Export': 'Cascavel', 'Estado': 'Parana', 'Municipio': 'Cascavel', 'ID_Ponto': 'Ponto_00001',
    'Latitude': LAT, 'Longitude': LON, 'Qualidade_Pixel': 'A'})])

# Dias do teste: um histórico, o primeiro provisório ERA5 e o primeiro dia de previsão GFS a partir de ontem
hoje = date.today()
bruto = (ee.ImageCollection(sp.SAB).filterBounds(geom).filterDate('2026-10-01', str(hoje + timedelta(days=17)))
         .map(lambda i: i.set('v', ee.Algorithms.If(i.propertyNames().contains('versao'), i.get('versao'), 'definitiva'))))
info = ee.Dictionary({'t': bruto.aggregate_array('system:time_start'), 'v': bruto.aggregate_array('v')}).getInfo()
escolhidos = {}
for t, v in sorted(zip(info['t'], info['v'])):
    d = str(date(1970, 1, 1) + timedelta(milliseconds=t))
    if v == 'provisoria_era5' and v not in escolhidos:
        escolhidos[v] = d
    if v.startswith('provisoria_gfs') and d >= str(hoje - timedelta(days=1)) and 'gfs' not in escolhidos:
        escolhidos['gfs'] = d
dias = [DIA_HISTORICO] + sorted(escolhidos.values())
print(f'Pixel ({LAT:.5f}, {LON:.5f}) | dias do teste: {", ".join(dias)} | versão da rotina {sp.VERSAO_ROTINA}')

ic = sp.colecao(geom, DIA_HISTORICO, str(date.fromisoformat(DIA_HISTORICO) + timedelta(days=1)))
for d in dias[1:]:
    ic = ic.merge(sp.colecao(geom, d, str(date.fromisoformat(d) + timedelta(days=1))))
ic = ic.sort('system:time_start')

# 1) A causa, direto no Earth Engine: nome da propriedade que o reduceRegions grava com 1 e com 2 bandas
img = ee.Image(ic.first())
um = img.select(['pr_mm']).reduceRegions(collection=grade, reducer=ee.Reducer.mean(), scale=sp.ESCALA_AREA)
dois = img.select(['pr_mm', 'tmax_C']).reduceRegions(collection=grade, reducer=ee.Reducer.mean(), scale=sp.ESCALA_AREA)
fix = img.select(['pr_mm']).reduceRegions(collection=grade, reducer=_novo(['pr_mm']), scale=sp.ESCALA_AREA)
nomes = ee.Dictionary({'um': ee.Feature(um.first()).toDictionary(), 'dois': ee.Feature(dois.first()).toDictionary(),
                       'fix': ee.Feature(fix.first()).toDictionary()}).getInfo()
base = set(grade.first().propertyNames().getInfo())
print('\n[1] Propriedades que o reduceRegions cria (sem as da grade):')
for k, rot in (('um', 'só pr_mm, redutor antigo '), ('dois', 'pr_mm + tmax_C, redutor antigo'), ('fix', 'só pr_mm, redutor NOVO   ')):
    print(f'    {rot}: {sorted(set(nomes[k]) - base)}')


def linhas(fc):
    return [{k: f['properties'].get(k) for k in f['properties']} for f in fc.getInfo()['features']]


def diario(cods, redutor):
    sp._redutor_media = redutor
    try:
        return linhas(sp.formatar(sp.linhas_diarias(ic, grade, sp.bandas_do_pedido(cods), sp.ESCALA_AREA),
                                  cods, sp.EXTRAS_DIARIA))
    finally:
        sp._redutor_media = _novo


def mensal(cods, redutor):
    sp._redutor_media = redutor
    try:
        saida = []
        for ini, fim, ano in MESES:
            icm = sp.colecao(geom, ini, fim)
            saida += linhas(sp.formatar(sp.linhas_mensais(icm, grade, ano, sp.bandas_do_pedido(cods), sp.ESCALA_AREA),
                                        cods, sp.EXTRAS_MENSAL))
        return saida
    finally:
        sp._redutor_media = _novo


falhas = 0
resumo = {}
for nome_res, func in (('DIÁRIO', diario), ('MENSAL', mensal)):
    print(f'\n[2] {nome_res}: cada variável pedida sozinha x o pedido "todas"')
    ref = {(l['Data_Completa'], l['Tipo_Dado']): l for l in func(sp.CODIGOS, _novo)}
    print(f'    {"variável":<40} {"data":<11} {"tipo":<20} {"todas":>9} {"antigo":>9} {"novo":>9}  resultado')
    for cod, col, *_ in sp.VARIAVEIS:
        antigo = {(l['Data_Completa'], l['Tipo_Dado']): l.get(col) for l in func([cod], _antigo)}
        novo = {(l['Data_Completa'], l['Tipo_Dado']): l.get(col) for l in func([cod], _novo)}
        for chave, lref in sorted(ref.items()):
            r, a, n = lref.get(col), antigo.get(chave), novo.get(chave)
            if r in (None, ''):
                res = 'sem dado no banco (esperado)' if n in (None, '') else 'FALHA: novo inventou valor'
            elif n == r and a in (None, ''):
                res = 'bug confirmado e corrigido'
                resumo.setdefault(col, set()).add(nome_res)
            elif n == r:
                res = 'ok (antigo já vinha preenchido)'
            else:
                res = 'FALHA: novo diferente de "todas"'
            falhas += res.startswith('FALHA')
            print(f'    {col:<40} {chave[0]:<11} {chave[1]:<20} {str(r):>9} {str(a or "(vazio)"):>9} '
                  f'{str(n or "(vazio)"):>9}  {res}')

print('\n[3] RESUMO')
for cod, col, *_ in sp.VARIAVEIS:
    print(f'    {col:<40} {"precisava da correção em: " + ", ".join(sorted(resumo[col])) if col in resumo else "não precisou (sem caso de coluna vazia)"}')
print(f'    {len(resumo)} de {len(sp.VARIAVEIS)} variáveis saíam vazias quando pedidas sozinhas.')
print('\n' + (f'❌ {falhas} FALHA(S)' if falhas else '✅ CORREÇÃO CONFIRMADA: toda variável pedida sozinha agora sai igual ao pedido "todas".'))
sys.exit(1 if falhas else 0)
