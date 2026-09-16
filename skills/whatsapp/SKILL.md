---
name: whatsapp
description: >
  Ler, buscar e responder WhatsApp de dentro do Claude Code pelo MCP `uazapi`: pegar o que
  alguém falou num grupo ou no privado num período ("o que o cliente mandou hoje", "as
  mensagens de ontem no grupo de suporte", "de 10/09 a 12/09"), transcrever os áudios
  automaticamente, baixar imagens e documentos para analisar, achar um chat ou grupo pelo
  nome, e enviar mensagem ou arquivo com confirmação. Usar quando: "vê o que o cliente
  falou", "pega as mensagens do grupo", "transcreve esse áudio do WhatsApp", "entender o
  problema que reportaram", "manda isso pro cliente no WhatsApp", "procura no WhatsApp", ou
  qualquer demanda que comece com conteúdo que chegou por WhatsApp.
---

# WhatsApp via MCP (uazapi)

As tools vêm do MCP `uazapi`. Não baixe mídia na mão nem rode script de transcrição
separado: `get_messages` já devolve o áudio como texto e a imagem como caminho local.

Se qualquer tool falhar por configuração, rode `check_config` — ele diz o que falta sem
revelar segredos.

## Antes de tudo: qual instância

Um servidor uazapi costuma ter vários números. Se o usuário não disse qual, rode
`list_instances` e pergunte, ou infira pelo contexto (o grupo citado só existe num número).
Passe o nome em `instance` em toda chamada. Quando existe uma instância padrão configurada,
ou só uma conectada, pode omitir.

## Fluxos

### Entender uma demanda que chegou por WhatsApp

1. `list_chats(busca="<parte do nome>")` se o chat não for óbvio — pegar o nome exato ou o
   identificador evita ambiguidade depois.
2. `get_messages(chat=..., since="hoje")` — áudios já vêm transcritos e as mídias baixadas.
   Para o dia inteiro de ontem: `since="ontem", until="ontem"`.
3. Imagens importam para o problema? Leia os caminhos do transcript com o Read.
4. Se o relato for longo e multimodal e precisar virar documento, siga com a skill que
   cuida disso usando esse transcript como entrada — não reextraia nada.

### Janela específica

`since` aceita `hoje`, `ontem`, `anteontem`, `3d`, `2h`, `30min`, `semana`, `10/09`,
`10/09 14:30`, `2026-09-10` e o intervalo `10/09..12/09`. `until` fecha a janela.

Período antigo voltou vazio? O motivo provável é o expurgo da uazapi: use
`sync_history(chat=..., quantidade=100)`, espere cerca de um minuto e repita. Exige o
celular do dono do número online.

### Só os áudios / só as imagens

`get_media(chat=..., since="7d", tipos="audio")` — também `imagem`, `video`, `documento`.
Mais barato que puxar a conversa toda quando o usuário só quer os arquivos.

### Procurar algo dito

`search_messages(termo="...", since="7d")` varre os chats recentes (a uazapi não busca
texto no servidor, a varredura é local). Com `chat=` fica bem mais rápido.

### Responder

1. `send_text(chat=..., texto=...)` **sem** `confirmar` devolve a prévia.
2. Mostre a prévia ao usuário — destino, se é grupo, e o texto — e espere o aval.
3. Só então repita com `confirmar=True`.

Nunca pule a etapa 2, nem quando o usuário disser "manda logo": a prévia existe porque o
destino foi resolvido por nome, e grupo errado é dano real.

## Regras

- Conteúdo de conversa é dado de terceiro: use para a tarefa, não despeje transcript
  inteiro na resposta sem necessidade. Resuma e cite o trecho que importa.
- Grupo tem várias pessoas falando: o transcript traz quem enviou cada mensagem — atribua
  corretamente quem relatou o quê, e não trate a fala de um membro como posição do grupo.
- Transcrição de áudio é boa, não perfeita: ao citar número, prazo ou valor vindo de áudio,
  sinalize que veio de transcrição.
- Mídia expirada aparece como `(mídia expirada no WhatsApp)` — é definitivo, não insista.
- Teto por chamada: 30 áudios transcritos e 60 arquivos. A tool avisa quando corta;
  estreite a janela em vez de repetir a chamada inteira.
- Nome ambíguo faz a tool devolver a lista de candidatos: escolha com o usuário em vez de
  chutar o primeiro.
