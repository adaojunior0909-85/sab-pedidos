# Testes da conversão CSV -> Excel (sem rede). Rodar: python testes/teste_sab_xlsx.py
# O GitHub Actions roda este arquivo antes de cada conversão: se algum teste falhar, nada é convertido.
import os
import re
import sys
import tempfile
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
import sab_xlsx as sx  # noqa: E402

falhas = 0


def confere(cond, msg):
    global falhas
    print(('  ok   ' if cond else '  FALHA ') + msg)
    falhas += 0 if cond else 1


CSV = ('Tipo_Dado,Versao_Algoritmo,Data_Completa,Ano,Mes,Dia,N_Ponto,Latitude,Longitude,Estado,Municipio,'
       'Precipitacao_mm,Umidade_Volumetrica_Solo_0_5cm_m3_m3,Qualidade_Pixel,Janela_Chuva_UTC,Confianca_Prazo,'
       'Fase_ENSO,RONI_Trimestre_C,Trimestre_CPC,Fonte_ENSO\n'
       'Historico_Observado,V1.0,2023-01-01,2023,01,01,Ponto_00001,-26.74951,-51.45034,Parana,Estado_Completo,'
       '18.40,0.405,A,12-12 UTC (D-1 a D),,La Nina,-0.6,DJF,CPC\n'
       'Previsao_GFS,V1.5,2026-11-10,2026,11,10,Ponto_00002,-26.74951,-51.35035,São José,Pato Branco,'
       ',0.410,A,00-24 UTC,alta,Indefinida,-,ASO,Persistencia\n')

print('[tipos das colunas]')
confere(sx.tipo_da_coluna('Precipitacao_mm') == 'numero' and sx.tipo_da_coluna('Latitude') == 'numero', 'números')
confere(sx.tipo_da_coluna('Ano') == 'inteiro' and sx.tipo_da_coluna('Data_Completa') == 'data', 'inteiros e datas')
confere(sx.tipo_da_coluna('Trimestre_CPC') == 'texto' and sx.tipo_da_coluna('Janela_Chuva_UTC') == 'texto' and
        sx.tipo_da_coluna('N_Ponto') == 'texto', 'textos continuam texto')
confere(sx.tipo_da_coluna('RONI_Trimestre_C') == 'numero' and sx.CASAS['RONI_Trimestre_C'] == 1, 'RONI com 1 casa')

print('[conversão]')
d = tempfile.mkdtemp()
c, x = os.path.join(d, 'a.csv'), os.path.join(d, 'a.xlsx')
open(c, 'w', encoding='utf-8').write(CSV)
n = sx.converter(c, x, 'teste')
confere(n == 2, '2 linhas de dados')
try:
    import openpyxl
    wb = openpyxl.load_workbook(x)
    ws = wb['Dados']
    cab = [ws.cell(1, j).value for j in range(1, ws.max_column + 1)]
    v = {cab[j - 1]: ws.cell(2, j) for j in range(1, len(cab) + 1)}
    confere(v['Precipitacao_mm'].value == 18.4 and v['Precipitacao_mm'].number_format == '0.00',
            'chuva 18.40 -> número 18,4 com 2 casas (aparece 18,40 no Excel em português)')
    confere(v['Umidade_Volumetrica_Solo_0_5cm_m3_m3'].number_format == '0.000', 'umidade com 3 casas')
    confere(v['Latitude'].value == -26.74951 and v['Ano'].value == 2023 and v['Mes'].value == 1, 'coordenadas e inteiros')
    confere(v['Data_Completa'].value.year == 2023 and v['Data_Completa'].number_format == 'dd/mm/yyyy', 'data como data')
    confere(v['Janela_Chuva_UTC'].value == '12-12 UTC (D-1 a D)' and v['RONI_Trimestre_C'].value == -0.6, 'texto e RONI')
    v2 = {cab[j - 1]: ws.cell(3, j).value for j in range(1, len(cab) + 1)}
    confere(v2['Precipitacao_mm'] is None and v2['RONI_Trimestre_C'] == '-' and v2['Estado'] == 'São José',
            'vazio fica vazio, "-" fica texto, acentos preservados (UTF-8)')
    confere(ws.freeze_panes == 'A2' and ws.auto_filter.ref is not None and 'Sobre' in wb.sheetnames,
            'cabeçalho congelado, filtro e aba Sobre')
except ImportError:
    xml = zipfile.ZipFile(x).read('xl/worksheets/sheet1.xml').decode('utf-8')
    confere(re.search(r'<c r="L2"[^>]*><v>18\.4</v>', xml) is not None, 'chuva como número (sem openpyxl)')

print('[recusa de planilha grande demais]')
velho = sx.LIMITE_LINHAS_EXCEL
sx.LIMITE_LINHAS_EXCEL = 1
try:
    sx.converter(c, x)
    confere(False, 'deveria recusar mais linhas que o limite do Excel')
except ValueError as e:
    confere('não cabe' in str(e), 'mais linhas que o Excel aceita: erro claro, o CSV fica')
sx.LIMITE_LINHAS_EXCEL = velho

print('[marcador para o Apps Script]')
m = sx.csv_do_marcador(sx.linhas_marcador([{'arquivo': 'A.xlsx', 'status': 'ok', 'linhas': 2},
                                           {'arquivo': 'B.xlsx', 'status': 'erro', 'detalhe': 'x, y'}], 'P1', 'ambos'))
confere(m.splitlines()[0] == 'Pedido,Arquivo,Status,Linhas,Detalhe,Modo,Gerado_em,Versao' and
        m.splitlines()[2].startswith('P1,B.xlsx,erro,,"x, y",ambos'), 'CSV do marcador com aspas')
confere(sx.atender('a b', 'x', 'ambos', True) == 2 and sx.atender('P0001', '1234567890ab', 'pdf', True) == 2,
        'ID, pasta e modo inválidos recusados antes do Drive')

print('[rotina inteira com um Drive simulado]')
APAGADOS, SUBIDOS = [], []


class Svc:
    def files(self):
        return self

    def delete(self, fileId):
        APAGADOS.append(fileId)
        return type('R', (), {'execute': lambda self_, **k: None})()


ITENS = [{'id': 'm', 'name': '00_Pedido_P0001.csv'}, {'id': 'd', 'name': '00_Dicionario_Variaveis_SAB.csv'},
         {'id': 'a', 'name': 'Diaria_Pato_Branco_2025.csv'}, {'id': 'b', 'name': 'Diaria_Pato_Branco_2026.csv'}]
sx.drive = lambda: Svc()
sx.listar = lambda svc, pid: list(ITENS)
sx.baixar = lambda svc, fid, dest: open(dest, 'w', encoding='utf-8').write(CSV if fid != 'b' else '')
sx.subir = lambda svc, pid, cam, nome, mime: SUBIDOS.append(nome) or 'x'
MARC = []
sx.subir_texto = lambda svc, pid, texto, nome: MARC.append((nome, texto)) or 'y'
confere(sx.atender('P0001', '1234567890ab', 'xlsx', False) == 0, 'terminou')
confere(SUBIDOS == ['00_Dicionario_Variaveis_SAB.xlsx', 'Diaria_Pato_Branco_2025.xlsx'], 'dicionário e dados em .xlsx')
confere(APAGADOS == ['a'], 'modo xlsx: só o CSV de dados convertido é apagado (manifesto, dicionário e o que falhou ficam)')
confere(MARC and MARC[0][0] == '00_Conversao_P0001.csv' and ',erro,' in MARC[0][1] and MARC[0][1].count(',ok,') == 2,
        'marcador com 2 ok e 1 erro (CSV vazio)')
ITENS.append({'id': 'z', 'name': '00_Conversao_P0001.csv'})
SUBIDOS.clear()
confere(sx.atender('P0001', '1234567890ab', 'ambos', False) == 0 and not SUBIDOS, 'rodar de novo não refaz (idempotente)')

print('\n' + (f'{falhas} FALHA(S)' if falhas else 'TODOS OS TESTES PASSARAM'))
sys.exit(1 if falhas else 0)
