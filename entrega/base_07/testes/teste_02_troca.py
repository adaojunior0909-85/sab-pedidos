# Testes offline da troca do asset RONI_CPC_v6 no 02 (v4): o bloco GRAVAR_ASSET roda contra um Earth Engine falso.
# Origem: simulação da auditoria independente B (cenários A a E), com as verificações transformadas em asserções.
# Rodar: python3 testes/teste_02_troca.py  (a partir da pasta do pacote)
import ast, io, json, types, numpy as np, pandas as pd, copy
import os
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_auditoria_roni_cpc.py')
src = open(SRC, encoding='utf-8').read(); tree = ast.parse(src)
class EEException(Exception): pass
R = 'projects/clima-492922/assets/RONI_CPC_v6'
class FakeData:
    def __init__(s, store, fail=()): s.store, s.fail = store, set(fail); s.log=[]
    def _f(s, op, *a):
        s.log.append((op,)+a)
        if (op,)+a in s.fail or op in s.fail: raise EEException(f'falha {op} {a}')
    def getAsset(s, p):
        if p not in s.store: raise EEException('not found')
        return {'id': p}
    def deleteAsset(s, p):
        s._f('delete', p)
        if p not in s.store: raise EEException('not found')
        del s.store[p]
    def renameAsset(s, a, b):
        s._f('rename', a, b)
        if a not in s.store or b in s.store: raise EEException('rename impossível')
        s.store[b] = s.store.pop(a)
    def getAssetAcl(s, p):
        if p not in s.store: raise EEException('nf')
        return copy.deepcopy(s.store[p]['acl'])
    def setAssetAcl(s, p, acl):
        s._f('setacl', p)
        if isinstance(acl, str): acl = json.loads(acl)
        s.store[p]['acl'] = dict(acl, owners=['user:eu'])
class FakeTask:
    def __init__(s, store, fc): s.store, s.fc = store, fc
    def start(s): s.store[R+'_TMP'] = {'dados': s.fc, 'acl': {'owners': ['user:eu']}}
    def status(s): return {'state': 'COMPLETED'}
def make_ee(store, fail=(), quebrar_leitura=False):
    ee = types.SimpleNamespace(); ee.EEException = EEException; ee.data = FakeData(store, fail)
    class FC:
        def __init__(s, x): s.x = x
        def size(s): return types.SimpleNamespace(getInfo=lambda: len(store[s.x]['dados']) if isinstance(s.x, str) else 0)
        def map(s, fn): return s
        def getInfo(s):
            feats = store[s.x]['dados']
            props = [dict(f) for f in feats]
            if quebrar_leitura: props = props[:-1]
            return {'features': [{'properties': p} for p in props]}
    def FeatureCollection(x):
        return FC(x)
    ee.FeatureCollection = FeatureCollection
    ee.Feature = lambda g, p: p
    ee.Geometry = types.SimpleNamespace(Point=lambda c: ('ponto', tuple(c)))   # [correção 23h55]
    ee.Algorithms = types.SimpleNamespace(If=lambda *a: None)
    ee.batch = types.SimpleNamespace(Export=types.SimpleNamespace(table=types.SimpleNamespace(
        toAsset=lambda collection, description, assetId: FakeTask(store, collection.x if isinstance(collection, FC) else collection))))
    return ee
# monta 'oficial'
ns0 = {'np': np, 'pd': pd, 'io': io, 'json': json}
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t,'id',None) in ('ORDEM','URL_TABELA_CPC','noaa_data','ASSET_RONI') for t in node.targets):
        exec(compile(ast.Module([node], []), SRC, 'exec'), ns0)
    if isinstance(node, ast.FunctionDef) and node.name in ('empate_2c','arred_sem_empate','ler_tabela','conciliar_oficial'):
        exec(compile(ast.Module([node], []), SRC, 'exec'), ns0)
tab = ns0['ler_tabela'](ns0['noaa_data'])
oficial, rel = ns0['conciliar_oficial'](tab, tab.rename(columns={'RONI':'RONI_2c'}))
oficial['data_ms'] = ((pd.to_datetime(dict(year=oficial['ano'], month=oficial['mes'], day=1)) - pd.Timestamp('1970-01-01')) // pd.Timedelta('1ms')).astype('int64')
oficial['chave_join'] = [f'{a:04d}_{m:02d}' for a, m in zip(oficial['ano'], oficial['mes'])]
cols = ['ano', 'mes', 'Trimestre', 'RONI', 'RONI_2c', 'Fonte', 'data_ms', 'chave_join']
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('asset_existe','acl_sem_dono','acl_resumo','aplicar_acl','ler_asset_roni','conferir_leitura')]
# o bloco da gravação (o 'if' da trava de sessão, também com GRAVAR_ASSET, fica de fora; correção 20/10 23h30)
bloco = [n for n in tree.body if isinstance(n, ast.If) and 'GRAVAR_ASSET' in ast.unparse(n.test)
         and '_escrita_bloqueada_na_sessao' not in ast.unparse(n.test)][0]
def rodar(store, fail=(), quebrar=False, rotulo=''):
    ee = make_ee(store, fail, quebrar)
    ns = dict(np=np, pd=pd, json=json, time=types.SimpleNamespace(sleep=lambda s: None), ee=ee, oficial=oficial.copy(),
              cols=cols, GRAVAR_ASSET=True, ASSET_RONI=R)
    for f in funcs: exec(compile(ast.Module([f], []), SRC, 'exec'), ns)
    # ee.FeatureCollection([...features]) no export: guarda a lista
    orig = ee.FeatureCollection
    ee.FeatureCollection = lambda x: orig(x) if isinstance(x, str) else types.SimpleNamespace(x=x)
    ee.batch.Export.table.toAsset = lambda collection, description, assetId: FakeTask(store, collection.x)
    import contextlib
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(ast.Module([bloco], []), SRC, 'exec'), ns)
        res = 'OK'
    except Exception as e:
        res = f'{type(e).__name__}: {str(e)[:400]}'
    print(f'--- {rotulo}: {res}')
    print('    assets finais:', {k.split('/')[-1]: (len(v['dados']), v['acl'].get('all_users_can_read')) for k, v in store.items()})
    print('    ops:', [o for o in ee.data.log if o[0] != 'setacl'][:8])
    return res, {k.split('/')[-1]: (len(v['dados']), v['acl'].get('all_users_can_read')) for k, v in store.items()}
antigo = [dict(r) for r in json.loads(oficial[cols].iloc[:-1].to_json(orient='records'))]
pub = {'owners': ['user:eu'], 'readers': [], 'writers': [], 'all_users_can_read': True}
N_NOVO, N_ANT = len(oficial), len(antigo)
FALHAS = []


def confere(cond, msg):
    print(('  ok   ' if cond else '  FALHA ') + msg)
    if not cond:
        FALHAS.append(msg)


r, f = rodar({}, rotulo='A primeira gravação, sem asset')
confere(r == 'OK' and f == {'RONI_CPC_v6': (N_NOVO, None)}, 'A: asset novo gravado, nada sobrando')
r, f = rodar({R: {'dados': antigo, 'acl': dict(pub)}}, rotulo='B troca normal com asset público')
confere(r == 'OK' and f == {'RONI_CPC_v6': (N_NOVO, True)}, 'B: asset novo no lugar, compartilhamento mantido, _ANTERIOR apagado')
r, f = rodar({R: {'dados': antigo, 'acl': dict(pub)}}, quebrar=True, rotulo='C conferência falha, restaura')
confere('restaurada' in r and f == {'RONI_CPC_v6': (N_ANT, True)}, 'C: versão anterior restaurada, compartilhamento mantido')
r, f = rodar({R + '_ANTERIOR': {'dados': antigo, 'acl': dict(pub)}}, quebrar=True,
             rotulo='D sobra _ANTERIOR (restauração anterior falhou) + conferência falha de novo')
confere('restaurada' in r and f == {'RONI_CPC_v6': (N_ANT, True)}, 'D (B-03): a única cópia boa não é perdida')
r, f = rodar({R + '_ANTERIOR': {'dados': antigo, 'acl': dict(pub)}}, rotulo='D2 sobra _ANTERIOR + conferência passa')
confere(r == 'OK' and f == {'RONI_CPC_v6': (N_NOVO, True)}, 'D2: troca completa a partir da sobra, compartilhamento mantido')
r, f = rodar({R: {'dados': antigo, 'acl': dict(pub)}}, fail=[('rename', R + '_TMP', R)], rotulo='E promoção do TMP falha')
confere(f.get('RONI_CPC_v6') == (N_ANT, True) and 'RONI_CPC_v6_ANTERIOR' not in f, 'E: asset anterior continua no lugar')
r, f = rodar({R: {'dados': antigo, 'acl': dict(pub)}}, quebrar=True, fail=[('delete', R)],
             rotulo='F conferência falha e o delete do asset ruim também')
confere('ainda existir, apague-o' in r and 'renomeie' in r, 'F (B-10): mensagem manda apagar antes de renomear')

print(f'\n{"TODOS OS TESTES PASSARAM" if not FALHAS else f"{len(FALHAS)} FALHA(S)"}')
import sys
sys.exit(1 if FALHAS else 0)
