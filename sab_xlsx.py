# >>> SAB: CONVERSÃO DOS CSV DE UM PEDIDO PARA EXCEL (.xlsx) (rotina do GitHub Actions). Versão 2026.11.01 <<<
# =========================================================================================
# O QUE FAZ
#   Quando todos os CSV de um pedido com formato "xlsx" ou "ambos" estão prontos, o Apps Script aciona esta rotina
#   (evento converter_xlsx). Ela baixa cada CSV da pasta SAB_pedido_<ID> do Google Drive, grava o mesmo conteúdo em
#   .xlsx com os NÚMEROS JÁ COMO NÚMEROS (o Excel mostra a vírgula decimal sozinho, em qualquer idioma) e as datas
#   como datas, e sobe o .xlsx para a mesma pasta. No fim grava 00_Conversao_<ID>.csv (o sinal para o Apps Script).
#     formato "ambos": ficam o CSV e o .xlsx de cada arquivo
#     formato "xlsx" : o CSV de dados é apagado depois que o .xlsx dele subiu (o manifesto e o dicionário ficam)
#   Nenhuma célula é recalculada: o valor do .xlsx é o texto do CSV convertido em número (18.40 -> 18,4 no Excel
#   em português, com formato de 2 casas: 18,40). Célula vazia continua vazia; "-" continua texto.
#
# EXECUÇÃO: GitHub Actions (.github/workflows/converter_xlsx.yml), com PEDIDO_ID, PASTA_ID (id da pasta no Drive),
#   MODO (xlsx ou ambos) e SIMULAR (1 = só lista o que faria). Usa a MESMA credencial do Earth Engine (segredo
#   EE_CREDENCIAL), que precisa da permissão do Google Drive (colab_credencial.py versão 3 confere isso).
# NÃO TOCA NO EARTH ENGINE. No Drive, só mexe na pasta do pedido indicada por PASTA_ID.
# =========================================================================================
import csv
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

VERSAO = '2026.11.01'
LIMITE_LINHAS_EXCEL = 1_048_575          # linhas de dados numa planilha do Excel (1.048.576 com o cabeçalho)
BRT = timezone(timedelta(hours=-3))
ARQ_CREDENCIAL = os.path.expanduser('~/.config/earthengine/credentials')
MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

csv.field_size_limit(10 ** 7)

# casas decimais de cada coluna numérica (as mesmas do CSV do painel)
try:
    import sab_pedido as _sp
    CASAS = {col: casas for _, col, _, casas, _ in _sp.VARIAVEIS}
except Exception:                        # rotina rodando sozinha (testes): as mesmas casas do painel
    CASAS = {}
CASAS.update({'Latitude': 5, 'Longitude': 5, 'RONI_Trimestre_C': 1})
INTEIRAS = {'Ano', 'Mes', 'Dia', 'N_Dias', 'Dias_no_Mes', 'Linhas_Esperadas'}
DATAS = {'Data_Completa'}
_NUM = re.compile(r'^-?\d+(\.\d+)?$')


# =========================================================================================
# CONVERSÃO (sem rede; testada em testes/teste_sab_xlsx.py)
# =========================================================================================
def tipo_da_coluna(nome):
    if nome in DATAS:
        return 'data'
    if nome in INTEIRAS:
        return 'inteiro'
    if nome in CASAS or re.search(r'_(mm|C|Porc|ms|MJ_m2|kPa|m3_m3)$', nome):
        return 'numero'
    return 'texto'


def converter(caminho_csv, caminho_xlsx, titulo=''):
    """CSV (UTF-8, vírgula, ponto decimal) -> .xlsx. Devolve o número de linhas de dados."""
    import xlsxwriter
    with open(caminho_csv, newline='', encoding='utf-8-sig') as f:
        leitor = csv.reader(f)
        cab = next(leitor, None)
        if cab is None:
            raise ValueError('CSV vazio')
        wb = xlsxwriter.Workbook(caminho_xlsx, {'constant_memory': True, 'strings_to_numbers': False,
                                                'strings_to_formulas': False, 'strings_to_urls': False})
        negrito = wb.add_format({'bold': True, 'bg_color': '#E7EFEA', 'border': 1})
        fmt_data = wb.add_format({'num_format': 'dd/mm/yyyy'})
        fmt_int = wb.add_format({'num_format': '0'})
        fmts = {}
        ws = wb.add_worksheet('Dados')
        tipos = [tipo_da_coluna(c) for c in cab]
        for j, c in enumerate(cab):
            if tipos[j] == 'numero':
                casas = CASAS.get(c, 2)
                fmts[j] = wb.add_format({'num_format': '0.' + '0' * casas if casas else '0'})
            ws.set_column(j, j, max(10, min(40, len(c) + 2)))
            ws.write_string(0, j, c, negrito)
        ws.freeze_panes(1, 0)
        n = 0
        for i, linha in enumerate(leitor, start=1):
            if i > LIMITE_LINHAS_EXCEL:
                wb.close()
                raise ValueError(f'mais de {LIMITE_LINHAS_EXCEL} linhas: não cabe numa planilha do Excel')
            for j, v in enumerate(linha[:len(cab)]):
                if v == '':
                    continue
                t = tipos[j]
                if t == 'data' and len(v) == 10 and v[4] == '-' and v[7] == '-':
                    try:
                        ws.write_datetime(i, j, datetime.strptime(v, '%Y-%m-%d'), fmt_data)
                        continue
                    except ValueError:
                        pass
                elif t in ('numero', 'inteiro') and _NUM.match(v):
                    ws.write_number(i, j, float(v), fmts.get(j, fmt_int))
                    continue
                ws.write_string(i, j, v)
            n = i
        ws.autofilter(0, 0, max(n, 1), len(cab) - 1)
        sobre = wb.add_worksheet('Sobre')
        sobre.set_column(0, 0, 110)
        for k, texto in enumerate([
                titulo or 'SAB - Banco de Dados Agrometeorológicos',
                f'Convertido do CSV em {datetime.now(BRT):%d/%m/%Y %H:%M} (rotina sab_xlsx {VERSAO}).',
                'Os números estão como números (o Excel mostra a vírgula decimal do seu idioma); as datas, como datas.',
                'Os valores são os mesmos do CSV: nenhuma célula foi recalculada. Célula vazia = sem dado.',
                'O significado de cada coluna está em 00_Dicionario_Variaveis_SAB.']):
            sobre.write_string(k, 0, texto)
        wb.close()
    return n


def linhas_marcador(resultados, pedido_id, modo):
    agora = f'{datetime.now(BRT):%Y-%m-%d %H:%M} (BRT)'
    return [{'Pedido': pedido_id, 'Arquivo': r['arquivo'], 'Status': r['status'], 'Linhas': str(r.get('linhas', '')),
             'Detalhe': r.get('detalhe', ''), 'Modo': modo, 'Gerado_em': agora, 'Versao': VERSAO} for r in resultados]


def csv_do_marcador(linhas):
    saida = io.StringIO()
    w = csv.DictWriter(saida, fieldnames=['Pedido', 'Arquivo', 'Status', 'Linhas', 'Detalhe', 'Modo', 'Gerado_em',
                                          'Versao'], lineterminator='\n')
    w.writeheader()
    w.writerows(linhas)
    return saida.getvalue()


# =========================================================================================
# GOOGLE DRIVE
# =========================================================================================
def drive():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    info = json.load(open(ARQ_CREDENCIAL, encoding='utf-8'))
    cid, csec = info.get('client_id'), info.get('client_secret')
    if not cid or not csec:
        from ee import oauth                 # cliente padrão do Earth Engine (o mesmo que gerou a credencial)
        cid, csec = cid or oauth.CLIENT_ID, csec or oauth.CLIENT_SECRET
    cred = Credentials(None, refresh_token=info['refresh_token'], token_uri='https://oauth2.googleapis.com/token',
                       client_id=cid, client_secret=csec)
    return build('drive', 'v3', credentials=cred, cache_discovery=False)


def listar(svc, pasta_id):
    itens, token = [], None
    while True:
        r = svc.files().list(q=f"'{pasta_id}' in parents and trashed = false", pageSize=1000, pageToken=token,
                             fields='nextPageToken, files(id, name, size, mimeType)').execute()
        itens += r.get('files', [])
        token = r.get('nextPageToken')
        if not token:
            return itens


def baixar(svc, arquivo_id, destino):
    from googleapiclient.http import MediaIoBaseDownload
    with open(destino, 'wb') as f:
        req = MediaIoBaseDownload(f, svc.files().get_media(fileId=arquivo_id), chunksize=50 * 1024 * 1024)
        feito = False
        while not feito:
            _, feito = req.next_chunk(num_retries=5)


def subir(svc, pasta_id, caminho, nome, mime):
    from googleapiclient.http import MediaFileUpload
    midia = MediaFileUpload(caminho, mimetype=mime, resumable=True, chunksize=50 * 1024 * 1024)
    return svc.files().create(body={'name': nome, 'parents': [pasta_id]}, media_body=midia, fields='id').execute(
        num_retries=5)['id']


def subir_texto(svc, pasta_id, texto, nome):
    from googleapiclient.http import MediaIoBaseUpload
    midia = MediaIoBaseUpload(io.BytesIO(texto.encode('utf-8')), mimetype='text/csv', resumable=False)
    return svc.files().create(body={'name': nome, 'parents': [pasta_id]}, media_body=midia, fields='id').execute(
        num_retries=5)['id']


def atender(pedido_id, pasta_id, modo, simular):
    t0 = time.time()
    print(f'📗 SAB, conversão para Excel | pedido {pedido_id} | modo {modo} | rotina {VERSAO} | '
          f'{"SIMULAÇÃO" if simular else "CONVERSÃO"}')
    if not re.match(r'^[A-Za-z0-9_-]{4,40}$', pedido_id or '') or not re.match(r'^[A-Za-z0-9_-]{10,80}$', pasta_id or ''):
        print('❌ PEDIDO_ID ou PASTA_ID inválido.')
        return 2
    if modo not in ('xlsx', 'ambos'):
        print('❌ MODO deve ser xlsx ou ambos.')
        return 2
    svc = drive()
    try:
        itens = listar(svc, pasta_id)
    except Exception as e:
        texto = str(e)
        print(f'❌ Não consegui ler a pasta no Drive: {texto[:300]}')
        if 'insufficient' in texto.lower() or '403' in texto:
            print('   A credencial do segredo EE_CREDENCIAL não tem a permissão do Google Drive. Gere de novo com o '
                  'colab_credencial.py (versão 3), marcando TODAS as caixas na tela de autorização.')
        return 1
    nomes = {x['name'] for x in itens}
    marcador = f'00_Conversao_{pedido_id}.csv'
    if marcador in nomes:
        print(f'♻️ {marcador} já existe: a conversão deste pedido já foi feita.')
        return 0
    csvs = sorted((x for x in itens if x['name'].endswith('.csv') and not x['name'].startswith('00_Pedido_')
                   and not x['name'].startswith('00_Conversao_')), key=lambda x: x['name'])
    print(f'   {len(csvs)} CSV para converter: ' + ', '.join(x['name'] for x in csvs[:8]) + ('...' if len(csvs) > 8 else ''))
    if simular:
        print('✅ SIMULAÇÃO: nada foi convertido.')
        return 0
    resultados = []
    tmp = os.environ.get('RUNNER_TEMP', '/tmp')
    for x in csvs:
        base = x['name'][:-4]
        nome_xlsx = base + '.xlsx'
        t1 = time.time()
        try:
            if nome_xlsx in nomes:
                resultados.append({'arquivo': nome_xlsx, 'status': 'ok', 'detalhe': 'já existia'})
                print(f'   ♻️ {nome_xlsx}: já existia')
                continue
            c, xl = os.path.join(tmp, 'entrada.csv'), os.path.join(tmp, 'saida.xlsx')
            baixar(svc, x['id'], c)
            n = converter(c, xl, titulo=f'SAB - pedido {pedido_id} - {base}')
            subir(svc, pasta_id, xl, nome_xlsx, MIME_XLSX)
            mb = os.path.getsize(xl) / 1e6
            resultados.append({'arquivo': nome_xlsx, 'status': 'ok', 'linhas': n, 'detalhe': f'{mb:.1f} MB'})
            print(f'   ✅ {nome_xlsx}: {n:,} linhas, {mb:.1f} MB, {time.time() - t1:.0f} s')
            if modo == 'xlsx' and not x['name'].startswith('00_'):
                svc.files().delete(fileId=x['id']).execute(num_retries=5)
                print(f'      🗑️ {x["name"]} apagado (pedido só em Excel)')
            for f_ in (c, xl):
                if os.path.exists(f_):
                    os.remove(f_)
        except Exception as e:
            resultados.append({'arquivo': nome_xlsx, 'status': 'erro', 'detalhe': str(e)[:200]})
            print(f'   ❌ {nome_xlsx}: {str(e)[:200]} (o CSV continua na pasta)')
    subir_texto(svc, pasta_id, csv_do_marcador(linhas_marcador(resultados, pedido_id, modo)), marcador)
    erros = sum(r['status'] != 'ok' for r in resultados)
    print(f'\n{"✅" if not erros else "⚠️"} {len(resultados) - erros} de {len(resultados)} arquivo(s) em Excel em '
          f'{(time.time() - t0) / 60:.1f} min. {marcador} gravado: o Apps Script entrega na próxima verificação.')
    return 0


if __name__ == '__main__':
    sys.exit(atender(os.environ.get('PEDIDO_ID', '').strip(), os.environ.get('PASTA_ID', '').strip(),
                     os.environ.get('MODO', 'ambos').strip().lower(),
                     os.environ.get('SIMULAR', '0').strip() in ('1', 'true', 'True')))
