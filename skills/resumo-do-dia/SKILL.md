---
name: resumo-do-dia
description: >
  Briefing do WhatsApp: varre as conversas recentes de um número e diz o que chegou, o que
  ainda está sem resposta e o que precisa de decisão — com os áudios já transcritos. Usar
  quando: "o que chegou hoje no WhatsApp", "resumo das conversas", "o que ficou sem
  responder", "me atualiza do WhatsApp", "tem algo pendente com os clientes". Requer o MCP
  `uazapi`.
---

# /resumo-do-dia

Para quando você passou o dia fora do WhatsApp e precisa saber o que aconteceu sem ler
tudo. O resultado é uma lista de pendências acionáveis, não um relatório.

## Workflow

### 1. Escolher o número

`list_instances` se o usuário não disse qual. Uma empresa costuma ter mais de um número
conectado, e o resumo do número errado é inútil.

### 2. Levantar as conversas com movimento

```
list_chats(tipo="all", limite=25, instance="<instância>")
```

A tabela vem ordenada pela última mensagem. Corte no ponto em que as conversas passam a
ser mais antigas que a janela pedida (padrão: hoje).

### 3. Ler cada conversa ativa

```
get_messages(chat="<chat>", since="hoje", limite=60, instance="<instância>")
```

Rode as leituras em sequência, mas não peça mídia onde não precisa: para conversas que só
têm texto, `baixar_midias=False` economiza tempo. Onde há áudio, deixe a transcrição ligada
— é o que revela o pedido real.

### 4. Classificar cada conversa

| Estado | Como identificar |
|---|---|
| **Aguardando você** | a última mensagem é do cliente e pede algo |
| **Aguardando o cliente** | a última é sua, com pergunta ou proposta em aberto |
| **Resolvido** | terminou em confirmação, agradecimento ou combinado fechado |
| **Ruído** | nada que exija ação |

### 5. Entregar o briefing

```markdown
# WhatsApp — {período} · {instância}

{N} conversas com movimento · {N} aguardando resposta sua

## Precisa de você
| Chat | Desde | O que pedem |
|---|---|---|
| nome | HH:MM | resumo em uma linha, com o pedido concreto |

## Aguardando o cliente
| Chat | Desde | O que você perguntou |
|---|---|---|

## Decisões que apareceram
- {algo que foi combinado, um prazo aceito, um preço acordado — com quem e quando}

## Resolvido hoje
{lista curta, uma linha cada}
```

## Regras

1. "Precisa de você" vem primeiro e é a única seção que pode ficar longa — o resto é
   contexto.
2. Cada linha de pendência diz **o que fazer**, não só o assunto. "Mandar a proposta
   revisada" em vez de "falou sobre a proposta".
3. Pedido que chegou por áudio: cite o trecho da transcrição, sinalizando a origem.
4. Não invente urgência. Se o cliente não pediu prazo, não escreva "urgente".
5. Grupo interno e conversa de cliente merecem separação — diga qual é qual.
6. Esta skill apenas lê. Para responder, use `send_text` com a prévia e o aval do usuário.
7. Nomes de clientes aparecem no briefing (é uso interno), mas não despeje transcript
   inteiro: o briefing é para decidir, não para reler o dia.
