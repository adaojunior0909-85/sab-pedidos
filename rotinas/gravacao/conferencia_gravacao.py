# Conferência da gravação (antes "saúde do banco"), toda semana (só LÊ o Earth Engine): o motor gravou nas últimas noites? Confere no SAB_V1 de 2026:
#   - dias seguidos, sem buraco e sem repetição, de 01/01/2026 até o fim da previsão;
#   - a previsão (GFS) chega a pelo menos hoje + 10 dias e o último dia ERA5 tem no máximo 10 dias de atraso;
#   - a hora em que o dia de hoje foi gravado: o motor roda toda noite (23h07), então ele não pode ter mais de 30 h;
#   - todos os dias de 2026 numa versão do algoritmo aceita (V1.6 ou V1.7: na troca, o motor refaz os dias aos poucos) e
#     o histórico (até 31/12/2025) sem versão nova.
#     python rotinas/gravacao/conferencia_gravacao.py
import os
import sys
from datetime import date, datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, os.path.dirname(os.path.dirname(AQUI)))
import ee  # noqa: E402
import estado  # noqa: E402
import sab_pedido as sp  # noqa: E402

VERSOES_ACEITAS = ('V1.6', 'V1.7')     # [24/11] a V1.7 refaz os dias de 2026 aos poucos depois da etapa B
MAX_HORAS_SEM_GRAVAR = 30
MIN_DIAS_PREVISAO = 10
MAX_ATRASO_ERA5 = 10


def main():
    ee.Initialize(project=sp.PROJETO)
    hoje = estado.agora().date()
    col = ee.ImageCollection(sp.SAB).filterDate('2026-01-01', '2028-01-01')
    lista = ee.List([col.aggregate_array('system:index'), col.aggregate_array('versao'),
                     col.aggregate_array('versao_algoritmo')]).getInfo()
    dias = [date(int(i[4:8]), int(i[9:11]), int(i[12:14])) for i in lista[0]]
    versoes = dict(zip(dias, lista[1]))
    algs = dict(zip(dias, lista[2]))
    problemas, resumo = [], []
    esperados = [date(2026, 1, 1) + timedelta(days=k) for k in range((max(dias) - date(2026, 1, 1)).days + 1)]
    buracos = sorted(set(esperados) - set(dias))
    repetidos = len(dias) - len(set(dias))
    if buracos or repetidos:
        problemas.append(f'{len(buracos)} dia(s) faltando (ex.: {", ".join(map(str, buracos[:3]))}) e {repetidos} repetido(s)')
    era5 = [d for d in dias if versoes[d] == 'provisoria_era5']
    gfs = [d for d in dias if str(versoes[d]).startswith('provisoria_gfs')]
    ult_era5, ult = max(era5) if era5 else None, max(dias)
    if ult < hoje + timedelta(days=MIN_DIAS_PREVISAO):
        problemas.append(f'a previsão vai só até {ult} (esperado: pelo menos {hoje + timedelta(days=MIN_DIAS_PREVISAO)})')
    if ult_era5 is None or (hoje - ult_era5).days > MAX_ATRASO_ERA5:
        problemas.append(f'último dia ERA5 = {ult_era5} (mais de {MAX_ATRASO_ERA5} dias de atraso)')
    fora = sorted({a for a in algs.values() if a not in VERSOES_ACEITAS})
    por_versao = {v: sum(1 for a in algs.values() if a == v) for v in sorted(set(algs.values()))}
    if fora:
        problemas.append(f'dias de 2026 com outra versão do algoritmo: {fora}')
    alvo = hoje if hoje in versoes else ult
    info = ee.data.getAsset(f"{sp.SAB}/SAB_{alvo:%Y_%m_%d}")
    gravado = datetime.fromisoformat(info['updateTime'].rstrip('Z').split('.')[0].split('+')[0]).replace(tzinfo=timezone.utc)
    horas = (datetime.now(timezone.utc) - gravado).total_seconds() / 3600
    if horas > MAX_HORAS_SEM_GRAVAR:
        problemas.append(f'o dia {alvo} foi gravado há {horas:.0f} h: o motor pode não ter rodado nas últimas noites')
    hist = ee.ImageCollection(sp.SAB).filterDate('1961-01-01', '2026-01-01').filter(
        ee.Filter.inList('versao_algoritmo', list(VERSOES_ACEITAS))).size().getInfo()
    if hist:
        problemas.append(f'{hist} dia(s) do histórico (até 2025) com a versão do motor de 2026: o histórico deveria estar travado')
    resumo.append(f"{len(dias)} dias de 2026 ({len(era5)} ERA5 até {ult_era5}, {len(gfs)} GFS até {ult}); "
                  f"dia {alvo} gravado há {horas:.0f} h; versões {por_versao}" + ('' if hist else '; histórico intocado'))
    if problemas:
        estado.registrar('gravacao', 'falhou', problemas + resumo)
        print('\n'.join(problemas))
        raise SystemExit(1)
    estado.registrar('gravacao', 'ok', resumo)
    print(resumo[0])


if __name__ == '__main__':
    main()
