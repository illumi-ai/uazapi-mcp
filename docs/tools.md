# Referência das tools

Todas as tools aceitam `instance` (nome, número ou token da instância). Vazio usa
`UAZAPI_DEFAULT_INSTANCE`; se não houver e só uma instância estiver conectada, usa essa;
caso contrário devolve um erro listando as conectadas.

Toda falha volta como texto começando com `ERRO:`, com o que fazer a seguir — nunca uma
exceção crua.

## check_config

Estado da configuração e teste de conexão. Não recebe parâmetros. Mostra quais variáveis
estão definidas (sem revelar valores), quantas instâncias existem e quais estão conectadas.

## list_instances

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `apenas_conectadas` | bool | `True` | `False` lista também as desconectadas |

## list_chats

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `busca` | str | `""` | Parte do nome do contato ou grupo |
| `tipo` | str | `"all"` | `all`, `group` ou `dm` |
| `limite` | int | `30` | Máximo de chats (teto da API: 100 por página) |

## list_groups

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `busca` | str | `""` | Filtra por nome ou JID |
| `limite` | int | `50` | Máximo de grupos |

## get_messages

A tool principal.

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `chat` | str | — | Nome do contato/grupo, número (`5562...`) ou JID completo |
| `since` | str | `""` | Início da janela. Aceita `10/09..12/09` como intervalo |
| `until` | str | `""` | Fim da janela (fecha às 23:59 quando é uma data) |
| `limite` | int | `300` | Teto de mensagens (máximo global: `MAX_MENSAGENS`) |
| `transcrever_audios` | bool | `True` | Áudios voltam como texto |
| `baixar_midias` | bool | `True` | Imagens/vídeos/documentos gravados em disco |
| `apenas_nossas` | bool | `False` | Só o que o número enviou (`fromMe`, filtra no servidor) |
| `tipo_mensagem` | str | `""` | Ex.: `AudioMessage`, `ImageMessage`, `DocumentMessage` |

Devolve o transcript agrupado por dia. Cada linha: `[data hora] autor: conteúdo`, com
`[audio] transcricao: "..."` e `arquivo: /caminho` quando houver mídia.

**Resolução de `chat`:** nome exato ganha; nome parcial ambíguo devolve a lista de
candidatos em vez de escolher sozinho; número é normalizado para JID.

## get_media

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `chat` | str | — | Como em `get_messages` |
| `since` / `until` | str | `""` | Janela de tempo |
| `tipos` | str | `"all"` | `all`, `audio`, `imagem`, `video` ou `documento` |
| `transcrever_audios` | bool | `True` | Transcreve os áudios encontrados |
| `limite` | int | `40` | Teto de arquivos (máximo global: `MAX_DOWNLOADS`) |

## search_messages

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `termo` | str | — | Texto procurado (case-insensitive) |
| `chat` | str | `""` | Vazio varre os chats mais recentes |
| `since` | str | `"7d"` | Profundidade da varredura |
| `limite_chats` | int | `15` | Quantos chats varrer quando `chat` está vazio |

A uazapi não busca texto no servidor: a varredura é local. Informar `chat` é bem mais rápido.

## get_chat_info

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `chat` | str | — | Contato ou grupo |

## sync_history

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `chat` | str | — | Conversa cujo histórico será pedido ao celular |
| `quantidade` | int | `100` | Mensagens antigas por chamada (teto da API: 100) |

Assíncrono: as mensagens aparecem no `get_messages` depois de alguns segundos ou minutos.
Exige o celular online. `HTTP 400` significa chat sem mensagem âncora conhecida.

## send_text

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `chat` | str | — | Destino |
| `texto` | str | — | Mensagem |
| `confirmar` | bool | `False` | `False` devolve prévia e **não envia** |
| `responder_id` | str | `""` | `messageid` a que a mensagem responde |

## send_media

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `chat` | str | — | Destino |
| `arquivo` | str | — | Caminho local ou URL |
| `tipo` | str | `"document"` | `image`, `video`, `document`, `audio`, `ptt`, `sticker` |
| `legenda` | str | `""` | Caption |
| `confirmar` | bool | `False` | `False` devolve prévia e **não envia** |

Arquivos locais são enviados em base64; URLs são repassadas à uazapi.

## mark_read

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `chat` | str | — | Conversa |
| `quantidade` | int | `20` | Últimas mensagens recebidas a marcar |

## react

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `chat` | str | — | Conversa |
| `message_id` | str | — | `messageid` alvo |
| `emoji` | str | `"👍"` | Vazio remove a reação |

## transcribe_file

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `caminho` | str | — | Arquivo de áudio local |
