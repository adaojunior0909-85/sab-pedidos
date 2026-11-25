# >>> SAB: lista dos municípios do GAUL 2015 para o formulário (GitHub Actions, rodar uma vez). Versão 2026.11.01 <<<
# Exporta para a pasta SAB_config do Drive o arquivo SAB_municipios_GAUL2015.csv (colunas Estado, Municipio), com os
# nomes EXATOS que a rotina sab_pedido.py procura. O montarFormulario do Apps Script lê esse arquivo e monta uma
# lista de municípios para cada estado: quem pede pelo formulário escolhe em vez de digitar.
# Só LÊ o Earth Engine (FAO/GAUL/2015/level2) e exporta 1 CSV. Não grava asset. Termina em 1 a 2 minutos; a
# exportação aparece na aba Tasks (SAB_lista_municipios) e o arquivo chega ao Drive em poucos minutos.
import time

import ee

PROJETO = 'clima-492922'
ee.Initialize(project=PROJETO)
mun = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM0_NAME', 'Brazil'))
fc = mun.map(lambda f: ee.Feature(None, {'Estado': f.get('ADM1_NAME'), 'Municipio': f.get('ADM2_NAME')})) \
    .distinct(['Estado', 'Municipio']).sort('Municipio').sort('Estado')
n = fc.size().getInfo()
print(f'📋 {n} municípios (Estado + Município distintos) no GAUL 2015 do Brasil')
t = ee.batch.Export.table.toDrive(collection=fc, description='SAB_lista_municipios', folder='SAB_config',
                                  fileNamePrefix='SAB_municipios_GAUL2015', fileFormat='CSV',
                                  selectors=['Estado', 'Municipio'])
t.start()
print(f'🚀 Exportação enviada: tarefa {t.id}')
for _ in range(60):
    estado = ee.data.getTaskStatus([t.id])[0].get('state')
    if estado in ('COMPLETED', 'SUCCEEDED', 'FAILED', 'CANCELLED'):
        break
    time.sleep(10)
print(f'   estado: {estado}')
if estado not in ('COMPLETED', 'SUCCEEDED'):
    raise SystemExit('❌ A exportação não terminou bem: confira a aba Tasks do Code Editor.')
print('✅ SAB_municipios_GAUL2015.csv na pasta SAB_config do Drive. Agora rode montarFormulario no Apps Script.')
