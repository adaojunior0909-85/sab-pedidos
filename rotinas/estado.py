# Painel de controle das rotinas automáticas do SAB (rotinas/PAINEL.md).
# Cada rotina grava o seu estado em rotinas/estado/<rotina>.json (registrar) e o painel é refeito a partir de todos
# os estados (montar_painel). Não fala com o Earth Engine.
#     python rotinas/estado.py                   refaz o PAINEL.md
#     python rotinas/estado.py piloto            lê pesquisa/piloto/ e registra o estado do piloto
import glob
import json
import os
import sys
from datetime import datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
PASTA_ESTADO = os.path.join(AQUI, 'estado')
PAINEL = os.path.join(AQUI, 'PAINEL.md')
BRT = timezone(timedelta(hours=-3))
SIMBOLO = {'ok': '✅', 'conferir': '👀', 'atencao': '⚠️', 'falhou': '❌', 'esperando': '⏳'}
# rotina: (nome, quando roda, o que fazer se der problema)
ROTINAS = {
    'saude': ('Saúde do banco (motor gravou?)', 'toda segunda-feira, 14h29',
              'Abra o Actions do sab-motor: a rodada da noite deu erro? Me mande o log.'),
    'roni': ('RONI do mês (02_auditoria_roni_cpc.py)', 'todo dia 11, 10h23',
             'Se parou num empate do CPC, o log diz qual valor digitar; me mande o log.'),
    'k26': ('K26, rodada 1 (2026 inteiro, só leitura)', 'todo dia 15, 15h41',
            'Compare com a execução anterior (colunas da tabela); me mande a pasta do resultado.'),
    'previsao': ('Acerto da previsão GFS (1 a 15 dias)', 'todo dia, 16h13',
                 'Me mande o log; a fotografia do dia que faltar só tira aquele dia da conta.'),
    'piloto': ('Piloto da previsão estendida (Tmin e Tmax)', 'dias 3 e 17, 08h17',
               'Leia pesquisa/piloto/CONFERENCIA.md quando aparecer.'),
}


def agora():
    return datetime.now(BRT)


def registrar(rotina, situacao, resumo, pasta='', detalhes=None):
    """Grava o estado de uma rotina e refaz o painel. situacao: ok, conferir, atencao, falhou ou esperando."""
    assert rotina in ROTINAS and situacao in SIMBOLO, (rotina, situacao)
    os.makedirs(PASTA_ESTADO, exist_ok=True)
    estado = {'rotina': rotina, 'quando': agora().strftime('%d/%m/%Y %H:%M'), 'situacao': situacao,
              'resumo': [str(x) for x in (resumo if isinstance(resumo, (list, tuple)) else [resumo])],
              'pasta': pasta, 'detalhes': detalhes or {}}
    with open(os.path.join(PASTA_ESTADO, f'{rotina}.json'), 'w', encoding='utf-8') as f:
        json.dump(estado, f, ensure_ascii=False, indent=1)
    montar_painel()
    return estado


def ler_estados():
    est = {}
    for arq in glob.glob(os.path.join(PASTA_ESTADO, '*.json')):
        with open(arq, encoding='utf-8') as f:
            e = json.load(f)
        est[e['rotina']] = e
    return est


def montar_painel():
    est = ler_estados()
    L = ['# Painel de controle das rotinas automáticas do SAB', '',
         f'Atualizado em {agora():%d/%m/%Y %H:%M} (Brasília). Cada rotina roda sozinha no GitHub Actions deste '
         'repositório e escreve aqui o último resultado. ✅ tudo certo · 👀 conferir os números · ⚠️ atenção · '
         '❌ falhou · ⏳ ainda não rodou.', '',
         '| Rotina | Quando roda | Última execução | Situação | Resumo |', '|---|---|---|---|---|']
    for r, (nome, quando, _) in ROTINAS.items():
        e = est.get(r)
        if e:
            L.append(f"| {nome} | {quando} | {e['quando']} | {SIMBOLO[e['situacao']]} | {e['resumo'][0]} |")
        else:
            L.append(f'| {nome} | {quando} | ainda não rodou | {SIMBOLO["esperando"]} | |')
    L += ['', '## Detalhes da última execução de cada rotina', '']
    for r, (nome, _, se_problema) in ROTINAS.items():
        e = est.get(r)
        L.append(f'### {nome}')
        if not e:
            L += ['', 'Ainda não rodou.', '']
            continue
        L += ['', f"{SIMBOLO[e['situacao']]} {e['quando']} (Brasília)", '']
        L += [f'- {x}' for x in e['resumo']]
        if e.get('pasta'):
            L.append(f"- Resultados: `{e['pasta']}`")
        if e['situacao'] in ('atencao', 'falhou'):
            L.append(f'- **O que fazer:** {se_problema}')
        L.append('')
    L += ['---', '', 'Se uma rotina falhar, o GitHub também manda um e-mail para quem juntou este arquivo na main. '
          'Para rodar uma rotina fora de hora: aba **Actions** → escolha a rotina na esquerda → **Run workflow**.']
    with open(PAINEL, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')


def estado_piloto():
    """Lê pesquisa/piloto/ (previsões emitidas e conferência) e registra."""
    pasta = os.path.join(RAIZ, 'pesquisa', 'piloto')
    prev = sorted(os.path.basename(a)[:-4] for a in glob.glob(os.path.join(pasta, 'previsoes', '*.csv')))
    conf = os.path.join(pasta, 'CONFERENCIA.md')
    resumo = [f'{len(prev)} emissão(ões); a última em {prev[-1]}' if prev else 'nenhuma emissão ainda']
    if os.path.exists(conf):
        linhas = [x for x in open(conf, encoding='utf-8').read().splitlines() if x.startswith('| ') and '---' not in x]
        resumo.append(f'conferência: {max(len(linhas) - 1, 0)} linha(s) em pesquisa/piloto/CONFERENCIA.md')
        situacao = 'conferir'
    else:
        resumo.append('conferência: ainda nenhuma (os períodos previstos ainda não terminaram ou o ERA5 não chegou)')
        situacao = 'ok' if prev else 'esperando'
    return registrar('piloto', situacao, resumo, 'pesquisa/piloto/')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'piloto':
        estado_piloto()
    else:
        montar_painel()
    print(open(PAINEL, encoding='utf-8').read())
