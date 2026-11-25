# Pacote SAB v41, atualização de 01/11/2026

Este zip traz TODOS os códigos do projeto, completos. O passo a passo está no guia publicado "Envio por e-mail SAB"
(versão 9) e em `automacao_email/Guia_Envio_Email_SAB.html` (passos U1 a U13).

## Mudou nesta atualização
| Arquivo | Versão | Onde vai |
|---|---|---|
| `automacao_email/sab_pedidos/sab_pedido.py` | 2026.11.01 | GitHub sab-pedidos |
| `automacao_email/sab_pedidos/sab_xlsx.py` (novo) | 2026.11.01 | GitHub sab-pedidos |
| `automacao_email/sab_pedidos/listar_municipios.py` (novo) | 2026.11.01 | GitHub sab-pedidos |
| `automacao_email/sab_pedidos/.github/workflows/*.yml` | 2026.11.01 | GitHub sab-pedidos |
| `automacao_email/sab_pedidos/testes/*`, `requirements.txt`, `README.md` | 2026.11.01 | GitHub sab-pedidos |
| `automacao_motor/sab-motor/*` (novo repositório público) | 2026.11.01 | GitHub sab-motor |
| `automacao_email/apps_script/Codigo.gs` | 2026.11.01 | Apps Script da planilha |
| `06_painel_sab_2026_10_7.js` | 2026.10.7 | Code Editor (script novo `SAB_painel_2026_10_7`; app teste1; oficial depois da K16) |
| `validacoes/K16_validacao_identidade_email.py` | K16 v3 (gera os CSV do painel sozinha) | Colab |
| `automacao_email/colab_credencial.py` | v3 | Colab |

## Não mudou (incluído para o pacote ficar completo)
01a/01b (máscara), 02 (RONI), 03/04 (matriz GFS), 05a/05b (motor V1.5: mesmos SHA-256 do pacote de 22/10, agora também
em `automacao_motor/sab-motor/`), 06 2026.10.4, 2026.10.5 e 2026.10.6 (histórico), 07a/07b (normais), 08 (auditoria), K8 a K15.

## Regras que continuam
Trava do histórico (PROTEGER_HISTORICO = True, até 2025-12-31); auditorias só leem; nunca rodar o `Código baselines.txt`;
sessão nova do Colab antes de script que grava; um script por vez e nunca junto com o motor (agora às 15h07 e 23h07 no
GitHub); números com ponto decimal; um arquivo por ano.

Conferência: `SHA256SUMS.txt` (todos os arquivos deste zip).
