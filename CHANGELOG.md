# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento:
[SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Corrigido

- Mídias de mensagens com o mesmo horário não se sobrescrevem mais. Áudios encaminhados
  juntos chegam com o mesmo `messageTimestamp`, e o arquivo era nomeado só por ele: das
  cópias, sobrava uma, e as outras mensagens apontavam para ela. O nome agora leva o id
  da mensagem.
- Download gravado em arquivo temporário e renomeado no fim, para a transcrição nunca
  ler um arquivo pela metade (era a causa de `Too much data for declared Content-Length`).
- O cache de transcrição passa a ser pelo conteúdo do áudio: o mesmo áudio encaminhado
  duas vezes é transcrito uma vez só, inclusive quando as cópias chegam juntas.

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
