# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento:
[SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado

- Transcrição pela OpenRouter (`/audio/transcriptions`), com `microsoft/mai-transcribe-2` como
  padrão: `OPENROUTER_API_KEY`, `UAZAPI_MCP_TRANSCRICAO_MODELO` e `UAZAPI_MCP_TRANSCRICAO`
  (`elevenlabs`, `openrouter` ou `desligada`). No automático, a ElevenLabs continua na frente
  quando a chave dela existe.
- A transcrição repete sozinha em 429 e 5xx, respeitando o `Retry-After`.
- `check_config` mostra qual provedor transcreve.

### Mudado

- Com `OPENROUTER_API_KEY` no ambiente e sem a chave da ElevenLabs, os áudios passam a ser
  transcritos (e cobrados) pela OpenRouter. Antes eram só baixados. Para manter como era:
  `UAZAPI_MCP_TRANSCRICAO=desligada`.

## [0.1.0] - 2026-09-16

Primeira versão.

### Adicionado

- 14 tools: leitura (chats, grupos, mensagens, mídias, busca, detalhes, sync), envio
  (texto, mídia, leitura, reação), transcrição avulsa e diagnóstico de configuração.
- Transcrição automática de áudios com ElevenLabs Scribe v2.
- Janelas de tempo em linguagem natural, resolvidas no cliente — a uazapi não filtra por
  data no servidor. Aceita com e sem acento (`mês`, `mes`).
- Envio em duas etapas: prévia com destino resolvido, depois confirmação.
- Multi-instância, com resolução por nome, número ou token.
- Três skills para Claude Code em `skills/`: `whatsapp`, `entender-problema` e
  `resumo-do-dia`.
- Workflow de release: a tag `vX.Y.Z` gera a release no GitHub com wheel e sdist.

### Segurança

- O `.env` do diretório de trabalho não é lido: o cliente MCP inicia o servidor dentro do
  projeto aberto, e um `.env` alheio não pode redirecionar `UAZAPI_SERVER` e o token junto.
- O `fileURL` da uazapi (público, sem autenticação) nunca circula: a mídia vai para o disco
  e só o caminho aparece. O httpx não loga mais as URLs no stderr.

[Unreleased]: https://github.com/illumi-ai/uazapi-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/illumi-ai/uazapi-mcp/releases/tag/v0.1.0
