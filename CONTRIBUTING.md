# Contribuindo

## Rodando localmente

```bash
uv sync
cp .env.example .env    # preencha com os dados da sua conta uazapi
uv run --group dev pytest
uv run uazapi-mcp
```

Os testes não fazem rede: cobrem o parser de janelas de tempo, a normalização de JID e a
montagem do transcript. Mudanças nessas partes precisam de teste junto.

## Ao mexer na API

Este projeto documenta o comportamento **medido** da uazapi, não o prometido. Se você
descobrir que um endpoint se comporta de outro jeito (por exemplo, que o filtro de data
passou a funcionar), atualize [`docs/api-uazapi.md`](docs/api-uazapi.md) com o teste que
mostra isso, e ajuste o código para aproveitar.

## Padrões

- Código e mensagens ao usuário em pt-BR; nomes de tools em inglês (convenção MCP).
- Toda tool devolve texto legível, e falha como `ERRO: <o que fazer>` em vez de exceção.
- Nada de tool que dispare mensagem sem a etapa de confirmação.
- Nunca commitar `.env`, mídias ou transcrições: são dados de terceiros.

## Abrindo uma issue

Inclua a versão do Python, o cliente MCP usado, a saída de `check_config` (ela já omite os
segredos) e, se for erro de API, o endpoint e o código HTTP.
