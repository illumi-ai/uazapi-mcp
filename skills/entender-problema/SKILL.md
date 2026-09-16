---
name: entender-problema
description: >
  Transforma o relato bagunçado de um cliente no WhatsApp — áudios, prints, vídeos e texto
  espalhados numa conversa — em um documento PROBLEMA estruturado, com timeline, quem
  reportou, evidências e severidade estimada. Usar quando: "entender o problema do cliente",
  "o que reportaram no grupo", "analisar esse relato de bug", "processar o feedback do
  cliente", ou antes de abrir uma issue/triagem a partir de conversa de WhatsApp. Requer o
  MCP `uazapi`.
---

# /entender-problema

Um cliente reporta um problema em cinco mensagens, dois áudios e um print. Esta skill lê
tudo isso e devolve um documento único que quem for corrigir consegue ler sem voltar na
conversa.

**Posição no fluxo:** `WhatsApp → /entender-problema → PROBLEMA → triagem/issue → correção`

## Ferramentas

- MCP `uazapi`: `list_chats`, `get_messages`, `get_media`
- Read tool para as imagens (o modelo lê print nativamente)
- Áudio **não** precisa de ferramenta extra: `get_messages` já devolve transcrito

## Entrada

| Parâmetro | Obrigatório | Default | Exemplo |
|---|---|---|---|
| Chat | sim | — | `"Empresa | Suporte"`, `5562...`, ou o JID |
| Janela | não | `24h` | `"48h"`, `"3d"`, `"ontem"`, `"10/09..12/09"` |
| Contexto | não | — | `"erro no login"`, `"não emite nota"` |
| Instância | se houver várias | — | nome do número que recebe as mensagens |

## Workflow

### 1. Resolver o chat

Nome parcial? `list_chats(busca="<nome>")` e confirme qual é antes de seguir. Se a tool
devolver vários candidatos, pergunte ao usuário em vez de escolher o primeiro.

### 2. Coletar a conversa

```
get_messages(chat="<chat>", since="24h", instance="<instância>")
```

Áudios já vêm como texto e imagens já vêm baixadas, com o caminho na linha da mensagem.

Ajuste a janela conforme o que voltar:
- menos de 3 mensagens relevantes → amplie para `48h`, depois `3d`
- muita conversa e contexto conhecido → `search_messages(termo=..., chat=...)` para achar
  onde o assunto começa, e então uma janela fechada em volta disso
- nada no período e o relato é antigo → `sync_history(chat=...)`, espere ~1 min, repita

### 3. Separar o que importa

| Categoria | O que é | Destino |
|---|---|---|
| Relato | descreve erro, comportamento inesperado, impacto | entra na timeline |
| Evidência | print, áudio, vídeo, documento | vira anexo |
| Ruído | "bom dia", "ok", "obrigado", combinados de horário | descarta |

### 4. Ler as evidências

- **Imagens**: Read no caminho que veio no transcript. Transcreva a mensagem de erro que
  aparece no print — é o dado mais útil do documento.
- **Áudios**: já transcritos. Se algum voltou como `[falha na transcrição: ...]`, use
  `transcribe_file` no caminho do arquivo.
- **Vídeos**: o MCP baixa mas não descreve. Use a ferramenta de análise de vídeo que você
  tiver, ou registre `[vídeo não analisado: <caminho>]` — nunca invente o conteúdo.
- Alguma mídia expirou no WhatsApp? Registre `[mídia expirada]` e siga.

### 5. Estimar severidade

| Nível | Indicadores |
|---|---|
| **P0** | "parou tudo", "ninguém consegue", tom urgente, várias pessoas reportando |
| **P1** | "não funciona", "dá erro", print de erro, funcionalidade central afetada |
| **P2** | "está estranho", "às vezes", função secundária, um relator |
| **P3** | sugestão, ajuste visual, "seria bom se", nada bloqueado |

O tom do áudio conta: transcrição não mostra irritação, mas a escolha de palavras mostra.

### 6. Escrever o documento

```markdown
# PROBLEMA

## Metadados
- **Chat**: {nome} ({grupo ou número})
- **Instância**: {número que recebeu}
- **Período**: {início} a {fim}
- **Mensagens**: {total} ({relevantes} relevantes, {n} com mídia)
- **Severidade estimada**: {P0-P3} — {justificativa em uma linha}

## Resumo
{3 a 5 frases cobrindo texto, áudios e prints. Auto-contido: quem ler entende o
problema sem abrir a conversa.}

## Timeline
| Hora | Quem | Tipo | Conteúdo |
|---|---|---|---|
| HH:MM | nome | texto | resumo |
| HH:MM | nome | áudio | resumo [ver A1] |
| HH:MM | nome | imagem | resumo [ver I1] |

## Quem reportou
| Pessoa | Mensagens | Papel |
|---|---|---|
| nome | N | reportou / confirmou / complementou |

## Indicadores de severidade
- **Palavras usadas**: termos exatos dos relatores
- **Quantas pessoas**: relatos independentes
- **O que está bloqueado**: impacto para o usuário ou para o negócio

## Anexos

### Áudios
**[A1]** {quem}, {HH:MM} — `{caminho do arquivo}`
> {transcrição completa, não resumida}

### Imagens
**[I1]** {quem}, {HH:MM} — `{caminho do arquivo}`
> {descrição; se for print de erro, a mensagem de erro transcrita literalmente}

## Relato para triagem
{1 ou 2 parágrafos condensados: o que quebrou, quem reportou, evidências com referência
aos anexos, severidade. Suficiente para abrir uma issue sem ler o resto.}
```

## Casos de borda

| Situação | O que fazer |
|---|---|
| Nenhuma mídia no período | Pular anexos, anotar "nenhuma mídia no período" |
| Só áudios | As transcrições são a fonte primária do resumo |
| Só prints | As descrições de imagem são a fonte primária |
| Mais de 100 mensagens | Filtrar por "erro", "bug", "problema", "não funciona", "parou" |
| Nada no período | Ampliar a janela; se continuar vazio, `sync_history` |
| Vários problemas na mesma conversa | Um documento por problema, não um documento confuso |
| Transcrição falhou | `transcribe_file` no caminho; se falhar de novo, registrar e seguir |

## Regras

1. Saída sempre em pt-BR.
2. Nunca fabricar: tudo vem de mensagem ou mídia real. Sem evidência, a linha não existe.
3. Transcrição de áudio vai completa no anexo, resumida só na timeline.
4. Esta skill **apenas lê**. Responder ao cliente é decisão do usuário, com `send_text` e
   sua confirmação.
5. Cada afirmação do resumo tem origem rastreável na timeline.
6. Ao citar número, prazo ou valor que veio de áudio, sinalize que veio de transcrição.
