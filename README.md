# sab-pedidos

Rotinas que atendem os pedidos de dados do **SAB – Banco de Dados Agrometeorológicos** (Google Earth Engine,
projeto `clima-492922`) enviados por e-mail. Repositório **privado**. Versão 2026.11.18.

Cada pedido chega do Apps Script da planilha do formulário (evento `repository_dispatch`) com só o **ID** e o
**código do pedido** (local, período, resolução, variáveis, filtro ENSO, formato). Nome e e-mail de quem pediu não
passam por aqui.

| Arquivo | O que é |
|---|---|
| `sab_pedido.py` | Valida o pedido, estima o tamanho antes de usar o Earth Engine, monta o mesmo cálculo do painel e envia as exportações (CSV) para a pasta `SAB_pedido_<ID>` do Drive |
| `sab_xlsx.py` | Converte os CSV de um pedido em Excel (.xlsx), com números e datas prontos (pedidos com formato xlsx ou ambos) |
| `listar_municipios.py` | Grava no Drive a lista de municípios do GAUL que o formulário usa (rodar uma vez) |
| `.github/workflows/pedido_sab.yml` | Evento `pedido_sab` (1 a 3 minutos por pedido) |
| `.github/workflows/converter_xlsx.yml` | Evento `converter_xlsx` (alguns minutos por milhão de linhas) |
| `.github/workflows/municipios.yml` | Manual: lista de municípios para o formulário |
| `testes/teste_sab_pedido.py`, `testes/teste_sab_xlsx.py` | Testes sem rede; rodam antes de cada execução |
| `testes/verificar_uma_variavel_ee.py`, `.github/workflows/verificar_correcao.yml` | Verificação com Earth Engine da correção 2026.11.18 (pedido de uma variável só saía com a coluna vazia); só lê, não exporta |
| `testes/fumaca_sab_pedido.py` | Execução completa com Earth Engine simulado (só para conferência local) |
| `requirements.txt` | `earthengine-api`, `xlsxwriter`, `openpyxl` |

**Segredo necessário:** `EE_CREDENCIAL` (Settings → Secrets and variables → Actions), gerado pelo
`colab_credencial.py` versão 3 (Earth Engine + Google Drive).

**Teste manual:** aba Actions → *Pedido SAB* → *Run workflow*. Com "Só simular" marcado, nada é exportado.

**Regra:** toda mudança no cálculo do painel exige mudar `sab_pedido.py` e repetir a validação K16
(identidade com o painel) antes de usar.
