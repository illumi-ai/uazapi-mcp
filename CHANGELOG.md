# Changelog

## 0.1.0

Primeira versão.

- 14 tools: leitura (chats, grupos, mensagens, mídias, busca, detalhes, sync), envio
  (texto, mídia, leitura, reação), transcrição avulsa e diagnóstico de configuração.
- Transcrição automática de áudios com ElevenLabs Scribe v2.
- Janelas de tempo em linguagem natural, resolvidas no cliente — a uazapi não filtra por
  data no servidor.
- Envio em duas etapas: prévia com destino resolvido, depois confirmação.
- Multi-instância, com resolução por nome, número ou token.
- Skill `whatsapp` para Claude Code incluída em `skills/`.
