# Notas sobre a API uazapi

Levantado contra a especificação completa (`https://docs.uazapi.com/openapi-bundled.json`,
132 endpoints, OpenAPI 3.1) e verificado com chamadas reais. O que está aqui foi medido,
não deduzido da documentação.

## Autenticação

Header `token` para operações de uma instância, `admintoken` para operações de servidor.
Este projeto só usa o `admintoken` em `/instance/all`, para listar instâncias e resolver o
token de cada uma pelo nome; todo o resto usa o token da instância.

## Endpoints usados

| Endpoint | Uso aqui |
|---|---|
| `GET /instance/all` | Lista instâncias e seus tokens (admintoken) |
| `POST /chat/find` | Busca chats, com operadores de filtro e ordenação |
| `POST /message/find` | Mensagens de um chat, paginadas |
| `POST /message/download` | Baixa a mídia de uma mensagem |
| `POST /message/history-sync` | Pede histórico antigo ao celular |
| `POST /chat/details` | Detalhes completos de contato ou grupo |
| `POST /group/list` | Grupos com busca e paginação |
| `POST /send/text`, `POST /send/media` | Envio |
| `POST /message/markread`, `POST /message/react` | Ações sobre mensagens |

## Filtros de `/chat/find`

Aceita operadores no valor do campo: `~` (contém), `!~` (não contém), `!=`, `>=`, `>`,
`<=`, `<`. Sem operador, o padrão é "contém". `operator: "OR"` junta os filtros com OU —
é como a busca por nome procura em `wa_contactName`, `wa_name` e `name` ao mesmo tempo.

Ordenação com `sort: "-wa_lastMsgTimestamp"`. Paginação com `limit` (máx. 100) e `offset`;
`pagination.totalRecords` traz o total.

## O que `/message/find` filtra — e o que não filtra

**Filtra no servidor:** `chatid`, `id`, `fromMe`, `messageType`, `track_source`, `track_id`.

Verificado: num grupo com 103 mensagens (102 recebidas, 1 enviada, 1 áudio),
`fromMe: true` devolveu exatamente 1 e `messageType: "AudioMessage"` devolveu exatamente 1.

**Não filtra:** data, em nenhuma grafia. Testado com `messageTimestamp: "<=<ts>"`,
`dateStart`/`dateEnd`, `timestamp_end` e `endDate` em ISO, todos com um corte na mediana do
chat: as quatro variações devolveram as mensagens mais recentes, ignorando o filtro. Busca
textual (`text: "~termo"`) também não filtra.

Consequência de projeto: janelas de tempo e busca textual são resolvidas no cliente,
paginando `/message/find` do mais recente para trás (`hasMore` + `nextOffset`) e parando
assim que aparece uma mensagem anterior ao início da janela.

## `/message/download`

`return_link: true` devolve `fileURL` servido pelo próprio servidor uazapi.
**Esse link é público**: uma requisição sem nenhum header de autenticação baixa o arquivo.
`generate_mp3` controla se o áudio volta em MP3 ou OGG.

O parâmetro `transcribe: true` depende de uma chave OpenAI configurada no servidor. Sem
ela, a resposta traz apenas `fileURL` e `mimetype`, sem campo de transcrição e sem erro.

## Ciclo de vida das mensagens

A instância não guarda histórico longo. Recém-conectada, enxerga poucos dias.
`/message/history-sync` pede ao celular (que precisa estar online) as mensagens anteriores
a uma âncora; é assíncrono, e as mensagens aparecem depois no `/message/find`. O histórico
sincronizado volta a ser expurgado em poucos dias, então qualquer coisa que precise durar
tem que ser salva fora da uazapi.

Mídia antiga expira nos servidores do WhatsApp e não é mais baixável, independente do sync.

## Campos relevantes

**Chat:** `wa_chatid`, `wa_contactName`, `name`, `wa_isGroup`, `wa_lastMsgTimestamp` (ms),
`wa_label`, `lead_status`, `owner`.

**Mensagem:** `messageid`, `messageTimestamp` (ms), `fromMe`, `senderName`, `sender`,
`messageType`, `text`, `quoted`, `content.caption`, `content.fileName`,
`content.fileSHA256` (hash do arquivo, base para deduplicação).

**Tipos vistos em produção:** `Conversation`, `ExtendedTextMessage`, `ImageMessage`,
`VideoMessage`, `AudioMessage`, `DocumentMessage`, `AlbumMessage`, `StickerMessage`,
`ReactionMessage`, `LocationMessage`, `ContactMessage`, `PtvMessage`.

## Endpoints deliberadamente fora deste MCP

A API cobre muito mais: disparo em massa (`/sender/*`), catálogo e perfil comercial
(`/business/*`), canais e newsletters (`/newsletter/*`), comunidades, etiquetas, CRM de
leads, proxy, integração com Chatwoot, chamadas de voz e webhooks (`/webhook`, `/sse`).
Nada disso serve ao objetivo aqui — trazer contexto de conversa para o agente e responder —
e disparo em massa é justamente o tipo de ferramenta que não deve ficar a uma chamada de
distância de um agente autônomo.
