# Roda o 02_auditoria_roni_cpc.py (sem mudança) no GitHub Actions e registra o resultado no painel de controle.
# O script é o mesmo do Colab: confere a tabela do CPC, acrescenta as estações novas, audita com o OISST e regrava o
# asset RONI_CPC_v6 com cópia de segurança e conferência (ele mesmo restaura a versão anterior se algo não bater).
#     python rotinas/roni/rodar_roni.py               grava o asset (a execução mensal, na main)
#     ROTINA_TESTE=1 python rotinas/roni/rodar_roni.py   só audita (GRAVAR_ASSET = False): o teste na branch
import io
import os
import re
import sys
import traceback

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import estado  # noqa: E402

SCRIPT = os.path.join(AQUI, '02_auditoria_roni_cpc.py')
TESTE = os.environ.get('ROTINA_TESTE') == '1'


class Tee(io.TextIOBase):
    def __init__(self, *saidas):
        self.saidas = saidas

    def write(self, s):
        for o in self.saidas:
            o.write(s)
            o.flush()
        return len(s)


def main():
    dia = estado.agora().strftime('%Y-%m-%d')
    pasta_rel = f'rotinas/resultados/roni/{dia}'
    pasta = os.path.join(estado.RAIZ, pasta_rel)
    os.makedirs(pasta, exist_ok=True)
    src = open(SCRIPT, encoding='utf-8').read()
    if TESTE:
        assert src.count('GRAVAR_ASSET = True ') == 1
        src = src.replace('GRAVAR_ASSET = True ', 'GRAVAR_ASSET = False', 1)
    log = open(os.path.join(pasta, 'LOG_RONI.txt'), 'w', encoding='utf-8')
    antes = sys.stdout
    sys.stdout = Tee(antes, log)
    erro = None
    try:
        os.chdir(pasta)                 # os CSV locais do script (RONI_CPC_v6.csv, auditoria_...) ficam no resultado
        exec(compile(src, SCRIPT, 'exec'), {'__name__': '__main__'})
    except BaseException as e:          # noqa: BLE001  (SystemExit também conta)
        erro = e
        print('\n' + traceback.format_exc())
    finally:
        sys.stdout = antes
        log.close()
    texto = open(os.path.join(pasta, 'LOG_RONI.txt'), encoding='utf-8').read()
    conferidas = re.findall(r'✅ (\d+) estações conferidas no asset', texto)
    acrescentadas = [x.strip() for x in re.findall(r'Estações acrescentadas do arquivo do CPC:[^\n]*', texto)]
    acrescentadas += [x.strip() for x in re.findall(r'⚠️ Revisão do CPC[^\n]*', texto)][:3]
    if erro is not None:
        ultima = [x for x in str(erro).splitlines() if x.strip()][-1:] or [type(erro).__name__]
        estado.registrar('roni', 'falhou', [f'parou: {ultima[0][:200]}', 'o asset anterior continua valendo'],
                         pasta_rel)
        raise SystemExit(1)
    if TESTE:
        resumo = ['teste (só auditoria; GRAVAR_ASSET = False): rodou sem erro; nada foi gravado']
    else:
        resumo = [f'asset RONI_CPC_v6 regravado e conferido ({conferidas[-1]} estações)' if conferidas
                  else 'rodou sem erro (veja o log)']
    resumo += acrescentadas
    estado.registrar('roni', 'ok', resumo, pasta_rel)


if __name__ == '__main__':
    main()
