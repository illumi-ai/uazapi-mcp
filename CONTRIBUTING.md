# Contribuindo

## Rodando localmente

```bash
uv sync
cp .env.example .env    # preencha com os dados da sua conta uazapi
uv run --group dev pytest
uv run --group dev ruff check src tests
uv run --env-file .env uazapi-mcp
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

## Release

A versão vive em um único lugar: `src/uazapi_mcp/__init__.py`. O `pyproject.toml` lê de lá.

1. Atualize `__version__` e mova o bloco `[Unreleased]` do `CHANGELOG.md` para a nova versão,
   com a data.
2. Commit, depois a tag: `git tag v0.2.0 && git push origin main v0.2.0`.
3. O workflow `release.yml` confere que a tag bate com `__version__`, roda os testes, gera
   wheel e sdist e cria a release no GitHub com as notas tiradas do CHANGELOG.

Publicação no PyPI é opcional e fica desligada por padrão. Para ligar: configure um
*trusted publisher* no PyPI apontando para este repositório e o workflow `release.yml`
(ambiente `pypi`), e crie a variável de repositório `PYPI_PUBLISH=true` no GitHub. A partir
daí toda tag publica, e a instalação vira `uvx uazapi-mcp`.

## Abrindo uma issue

Inclua a versão do Python, o cliente MCP usado, a saída de `check_config` (ela já omite os
segredos) e, se for erro de API, o endpoint e o código HTTP.
