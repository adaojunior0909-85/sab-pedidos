# sab-pedidos

Rotina que atende os pedidos de dados do **SAB – Banco de Dados Agrometeorológicos** (Google Earth Engine,
projeto `clima-492922`) enviados por e-mail. Repositório **privado**.

Cada pedido chega do Apps Script da planilha do formulário (evento `repository_dispatch`, tipo `pedido_sab`) com
só o **ID** e o **código do pedido** (local, período, resolução, variáveis). Nome e e-mail de quem pediu não
passam por aqui.

| Arquivo | O que é |
|---|---|
| `sab_pedido.py` | Valida o pedido, monta o mesmo cálculo do painel 2026.10.4 e envia as exportações para a pasta `SAB_pedido_<ID>` do Drive |
| `.github/workflows/pedido_sab.yml` | A execução no GitHub Actions (1 a 3 minutos por pedido) |
| `testes/teste_sab_pedido.py` | Testes sem Earth Engine; rodam antes de cada pedido |
| `testes/fumaca_sab_pedido.py` | Execução completa com Earth Engine simulado (só para conferência local) |
| `requirements.txt` | `earthengine-api` |

**Segredo necessário:** `EE_CREDENCIAL` (Settings → Secrets and variables → Actions), com o conteúdo do arquivo
de credencial do Earth Engine da conta dona do projeto.

**Teste manual:** aba Actions → *Pedido SAB* → *Run workflow*. Com "Só simular" marcado, nada é exportado.

**Regra:** toda mudança no cálculo do painel exige mudar `sab_pedido.py` e repetir a validação K16
(identidade com o painel) antes de usar.
