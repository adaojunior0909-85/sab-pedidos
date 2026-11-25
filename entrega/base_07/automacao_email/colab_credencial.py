# >>> SAB: gera a credencial do Earth Engine para o GitHub (versão 3). Rode numa sessão NOVA do Colab, sozinha. <<<
# Abre um link de autorização do Google: entre com a conta dona do projeto clima-492922. Na página de
# autorização, MARQUE TODAS AS CAIXAS (Earth Engine, Cloud e Google Drive) e NÃO marque acesso somente leitura:
# a rotina precisa iniciar exportações e a conversão para Excel precisa ler e gravar na pasta do pedido no Drive.
# Copie o código mostrado e cole na caixa que aparece abaixo da célula.
# [v3, 01/11/2026] Confere também o acesso ao Google Drive (lista 1 arquivo, sem abrir nem mudar nada).
# A MESMA linha vai para o segredo EE_CREDENCIAL dos DOIS repositórios: sab-pedidos e sab-motor.
import json
import os

import ee

ESCOPOS = ['https://www.googleapis.com/auth/earthengine',
           'https://www.googleapis.com/auth/cloud-platform',
           'https://www.googleapis.com/auth/drive',
           'https://www.googleapis.com/auth/devstorage.full_control']
try:
    ee.Authenticate(auth_mode='notebook', scopes=ESCOPOS, force=True)
except TypeError:                      # versão da biblioteca sem o parâmetro scopes
    ee.Authenticate(auth_mode='notebook', force=True)
ee.Initialize(project='clima-492922')
ee.Number(1).getInfo()

cred = json.load(open(os.path.expanduser('~/.config/earthengine/credentials'), encoding='utf-8'))
escopos = cred.get('scopes', [])
so_leitura = [s for s in escopos if 'readonly' in s or 'read_only' in s or 'read-only' in s]

drive_ok, drive_erro = False, ''
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from ee import oauth
    c = Credentials(None, refresh_token=cred['refresh_token'], token_uri='https://oauth2.googleapis.com/token',
                    client_id=cred.get('client_id') or oauth.CLIENT_ID,
                    client_secret=cred.get('client_secret') or oauth.CLIENT_SECRET)
    build('drive', 'v3', credentials=c, cache_discovery=False).files().list(pageSize=1, fields='files(id)').execute()
    drive_ok = True
except Exception as e:
    drive_erro = str(e)[:200]

if so_leitura or 'https://www.googleapis.com/auth/earthengine' not in escopos:
    print('❌ A credencial saiu SOMENTE LEITURA:', ', '.join(so_leitura or escopos))
    print('   Com ela a rotina não consegue exportar. Rode a célula de novo e, na página de autorização,')
    print('   não marque a opção de acesso somente leitura (read-only).')
elif not drive_ok:
    print('❌ A credencial não tem acesso ao Google Drive:', drive_erro)
    print('   Sem ele, a conversão para Excel não funciona. Rode a célula de novo e, na página de autorização,')
    print('   marque TODAS as caixas (inclusive a do Google Drive).')
else:
    print('✅ Credencial com permissão de exportar (Earth Engine) e de usar o Google Drive, projeto clima-492922.')
    print('Copie a LINHA INTEIRA abaixo (começa com { e termina com }) e cole no segredo EE_CREDENCIAL dos dois')
    print('repositórios do GitHub (sab-pedidos e sab-motor):')
    print('-' * 70)
    print(json.dumps(cred, ensure_ascii=False))
    print('-' * 70)
    print('Depois de colar no GitHub: Editar > Limpar todas as saídas. Não salve, não fotografe e não compartilhe esta saída.')
