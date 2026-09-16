# uazapi-mcp — instruções para agentes

Servidor MCP em Python que lê, transcreve e envia mensagens de WhatsApp pela API uazapi.
O usuário final é um agente (Claude Code ou outro cliente MCP); tudo que o servidor devolve
é texto para o agente ler.

## Mapa

| Arquivo | Papel |
|---|---|
| `src/uazapi_mcp/server.py` | As 14 tools. Cada uma resolve instância → chat → chama a API → formata |
| `src/uazapi_mcp/uazapi.py` | Cliente HTTP (retry, erros), resolução de instância e de chat |
| `src/uazapi_mcp/midia.py` | Download para disco e transcrição (ElevenLabs Scribe v2) |
| `src/uazapi_mcp/ranges.py` | Datas em linguagem natural → timestamps. Sem rede |
| `src/uazapi_mcp/formato.py` | Transcript e tabelas em Markdown. Sem rede |
| `src/uazapi_mcp/config.py` | Variáveis de ambiente e `.env`. Nunca lê o `.env` do cwd |
| `docs/api-uazapi.md` | Comportamento **medido** da API. Leia antes de mexer em qualquer chamada |
| `docs/tools.md` | Referência de parâmetros. Atualize junto com `server.py` |
| `skills/` | Skills de Claude Code que ensinam os fluxos. Genéricas: sem nomes de clientes |

## Comandos

```bash
uv sync
uv run --group dev pytest -q             # testes sem rede; obrigatório antes de commitar
uv run --group dev ruff check src tests  # lint; o CI reprova se falhar
uv run --env-file .env uazapi-mcp        # servidor em stdio, com credenciais do .env local
```

Para testar contra a API real, as credenciais ficam em `~/.uazapi-mcp/.env` ou no `.env` do
clone passado com `--env-file`. Prefira `check_config`, `list_instances` e `list_chats`,
que são baratos. `get_messages` e `get_media` baixam mídia e gastam créditos de
transcrição: rode com janela curta e só quando a mudança exige.

## Convenções

- **pt-BR com acentos** em tudo que o usuário ou o modelo lê: docstrings (viram descrição
  da tool), mensagens de erro, saída das tools, comentários. Nomes de tools, parâmetros e
  identificadores ficam como estão.
- **Valores de parâmetro são ASCII** (`tipos="audio"`, `since="mes"`). A entrada passa por
  `ranges.normalizar`, então acento na chamada não quebra nada — mas não acentue os
  literais de comparação.
- **Toda tool devolve texto.** Falha é `ERRO: <o que fazer a seguir>`, nunca exceção.
- **Envio é em duas etapas.** `confirmar=False` devolve prévia e não envia. Não existe
  caminho que dispare mensagem sem isso, e não deve passar a existir.
- **Nada de disparo em massa.** `/sender/*` fica fora de propósito.
- Ao descobrir que a API se comporta diferente do documentado em `docs/api-uazapi.md`,
  atualize o documento com o teste que prova, e só então o código.
- Testes cobrem as partes puras (`ranges`, `formato`, `jid_de`). Mudança nelas vem com
  teste. Não há testes de rede e não deve haver: rodam no CI sem credenciais.

## Segurança — regras que não se negociam

- Token nunca aparece em log, erro ou saída. `config.diagnostico()` mascara; mantenha.
- O `fileURL` da uazapi é público sem autenticação. A mídia vai para o disco e só o
  caminho circula. Não devolva o link, não o logue.
- Nomes vindos da API (chat, instância, arquivo) passam por `midia._slug` antes de virar
  caminho. Não construa caminhos com valor cru.
- O `.env` do diretório de trabalho não é lido. Não reintroduza: o cliente MCP inicia o
  servidor no cwd do projeto aberto, e um `.env` alheio poderia redirecionar o token.
- Nunca commitar `.env`, `media/`, transcrições ou trechos de conversa real. Testes usam
  números fictícios (`5511999990000`, `120363000000000001@g.us`).

## Release

Versão única em `src/uazapi_mcp/__init__.py`. Atualize `__version__`, mova o bloco
`[Unreleased]` do `CHANGELOG.md` para a versão com data, commit, e então
`git tag vX.Y.Z && git push origin main vX.Y.Z`. O workflow `release.yml` confere a tag,
roda testes e lint, e cria a release no GitHub com wheel e sdist. Detalhes em
`CONTRIBUTING.md`.
