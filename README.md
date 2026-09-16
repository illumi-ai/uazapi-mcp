<div align="center">

# uazapi-mcp

**Seu WhatsApp dentro do Claude Code — com os áudios já transcritos.**

[![tests](https://github.com/illumi-ai/uazapi-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/illumi-ai/uazapi-mcp/actions/workflows/tests.yml)
[![release](https://img.shields.io/github/v/release/illumi-ai/uazapi-mcp?label=release&color=2ea44f)](https://github.com/illumi-ai/uazapi-mcp/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![MCP](https://img.shields.io/badge/MCP-server-8A2BE2.svg)](https://modelcontextprotocol.io)

Servidor MCP para ler, transcrever e enviar mensagens de WhatsApp pela [uazapi](https://docs.uazapi.com/).

</div>

---

## O problema que isso resolve

Um cliente manda um áudio de dois minutos explicando um bug, mais três prints. Hoje o
caminho é: abrir o WhatsApp, baixar o áudio, mover para uma pasta, rodar alguma ferramenta
de transcrição, baixar cada imagem, copiar tudo para o agente — e só então começar a
trabalhar.

Com este MCP, é uma pergunta:

```
> o que o cliente falou no grupo Suporte hoje?

[09:12] Marcos: [áudio] transcrição: "Bom dia, o sistema travou na hora de emitir a
  nota, aparece um erro de conexão e não deixa salvar o pedido. Já tentei três vezes..."
[09:14] Marcos: [imagem] arquivo: ~/.uazapi-mcp/media/comercial/suporte/1757930040000-image.jpg
[09:15] NÓS: Já estamos olhando, Marcos.
```

O áudio volta como texto. A imagem volta como arquivo local, pronto para o agente abrir.

## O que dá para fazer

| Você pede | O que acontece |
|---|---|
| *"o que chegou do cliente X hoje"* | Conversa do dia, áudios transcritos, prints baixados |
| *"as mensagens do grupo entre 10/09 e 12/09"* | Janela fechada, agrupada por dia |
| *"só os áudios da última semana"* | Filtra por tipo no servidor e transcreve cada um |
| *"procura onde falaram de reembolso"* | Varredura nas conversas recentes |
| *"manda esse resumo pro cliente"* | Prévia com destino resolvido → sua confirmação → envio |
| *"quais grupos eu tenho?"* | Lista com identificadores |

## Instalação

Precisa de [uv](https://docs.astral.sh/uv/), `git` e Python 3.11+. **Não precisa clonar** — o
`uvx` baixa e roda direto do repositório:

```bash
claude mcp add uazapi \
  --env UAZAPI_SERVER=https://suaempresa.uazapi.com \
  --env UAZAPI_ADMIN_TOKEN=seu_admin_token \
  --env ELEVENLABS_API_KEY=sua_chave_elevenlabs \
  -- uvx --from git+https://github.com/illumi-ai/uazapi-mcp uazapi-mcp
```

Para fixar uma versão, troque a origem por `git+https://github.com/illumi-ai/uazapi-mcp@v0.1.0`.
As versões estão em [Releases](https://github.com/illumi-ai/uazapi-mcp/releases), cada uma com
wheel e sdist anexados.

Reinicie a sessão e peça ao agente para rodar `check_config` — ele confirma a conexão e
lista as instâncias conectadas, sem revelar segredos.

<details>
<summary><b>Outros clientes MCP</b> (Claude Desktop, Cursor, Windsurf…)</summary>

```json
{
  "mcpServers": {
    "uazapi": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/illumi-ai/uazapi-mcp", "uazapi-mcp"],
      "env": {
        "UAZAPI_SERVER": "https://suaempresa.uazapi.com",
        "UAZAPI_ADMIN_TOKEN": "seu_admin_token",
        "ELEVENLABS_API_KEY": "sua_chave_elevenlabs"
      }
    }
  }
}
```

</details>

### Skills (recomendado)

O repositório traz três skills que ensinam ao agente os fluxos completos:

| Skill | Para que serve |
|---|---|
| **`whatsapp`** | Ler, buscar, baixar mídia e responder. A base |
| **`entender-problema`** | Relato espalhado do cliente vira documento estruturado, com timeline, evidências e severidade |
| **`resumo-do-dia`** | Briefing: o que chegou, o que está sem resposta, o que precisa de decisão |

```bash
git clone https://github.com/illumi-ai/uazapi-mcp
cp -r uazapi-mcp/skills/whatsapp uazapi-mcp/skills/entender-problema uazapi-mcp/skills/resumo-do-dia ~/.claude/skills/
```

Detalhes e como adaptar ao seu fluxo em [`skills/README.md`](skills/README.md).

## Configuração

| Variável | Obrigatória | Para que serve |
|---|---|---|
| `UAZAPI_SERVER` | **sim** | Servidor da sua conta, ex.: `https://suaempresa.uazapi.com` |
| `UAZAPI_ADMIN_TOKEN` | sim¹ | Lista as instâncias e resolve o token de cada uma pelo nome |
| `UAZAPI_TOKEN` | sim¹ | Alternativa: token de **uma** instância, se você só tem acesso a ela |
| `UAZAPI_DEFAULT_INSTANCE` | não | Instância usada quando a chamada não informa `instance` |
| `ELEVENLABS_API_KEY` | não | Transcrição ([Scribe v2](https://elevenlabs.io/speech-to-text)). Sem ela o áudio é baixado, não transcrito |
| `UAZAPI_MCP_MEDIA_DIR` | não | Onde gravar as mídias (padrão `~/.uazapi-mcp/media`) |
| `UAZAPI_MCP_MAX_MENSAGENS`<br>`UAZAPI_MCP_MAX_TRANSCRICOES`<br>`UAZAPI_MCP_MAX_DOWNLOADS` | não | Tetos por chamada: `3000` / `30` / `60` |

¹ Um dos dois. Ambos os tokens saem do painel da uazapi.

As variáveis também podem ficar num `.env` em `~/.uazapi-mcp/.env` ou em `~/.claude/.env`,
nessa ordem e sempre atrás das variáveis já exportadas. Copie de
[`.env.example`](.env.example). O `.env` do diretório de trabalho **não** é lido: o cliente
MCP inicia o servidor dentro do projeto aberto, e um `.env` de terceiros não pode apontar
`UAZAPI_SERVER` — e o token junto — para outro lugar.

## Tools

<table>
<tr><th colspan="2" align="left">Leitura</th></tr>
<tr><td><code>check_config</code></td><td>Estado da configuração e teste de conexão, sem revelar segredos</td></tr>
<tr><td><code>list_instances</code></td><td>Números disponíveis no servidor e quais estão conectados</td></tr>
<tr><td><code>list_chats</code></td><td>Conversas por recência, com busca por nome e filtro grupo/individual</td></tr>
<tr><td><code>list_groups</code></td><td>Grupos de que o número participa, com identificador</td></tr>
<tr><td><b><code>get_messages</code></b></td><td><b>A principal.</b> Conversa numa janela de tempo, áudios transcritos e mídias baixadas</td></tr>
<tr><td><code>get_media</code></td><td>Só os arquivos de um período, por tipo</td></tr>
<tr><td><code>search_messages</code></td><td>Procura um termo nas mensagens recentes</td></tr>
<tr><td><code>get_chat_info</code></td><td>Detalhes de um contato ou grupo</td></tr>
<tr><td><code>sync_history</code></td><td>Pede ao celular o histórico que a uazapi já expurgou</td></tr>
<tr><th colspan="2" align="left">Envio</th></tr>
<tr><td><code>send_text</code></td><td>Envia texto — confirmação em duas etapas</td></tr>
<tr><td><code>send_media</code></td><td>Envia arquivo ou URL — confirmação em duas etapas</td></tr>
<tr><td><code>mark_read</code></td><td>Marca as últimas mensagens como lidas</td></tr>
<tr><td><code>react</code></td><td>Reage a uma mensagem</td></tr>
<tr><td><code>transcribe_file</code></td><td>Transcreve um áudio local</td></tr>
</table>

Parâmetros completos em [`docs/tools.md`](docs/tools.md).

### Datas em português

`get_messages`, `get_media` e `search_messages` entendem data como gente fala:

| Expressão | Significado |
|---|---|
| `hoje`, `ontem`, `anteontem` | O dia inteiro (repita em `until` para fechar) |
| `2h`, `30min`, `3d`, `1 semana` | A partir de agora |
| `semana`, `mes` | Desde o início da semana/mês corrente |
| `10/09`, `10/09/2026`, `10/09 14:30` | Data brasileira, hora opcional |
| `2026-09-10 14:30` | ISO |
| `10/09..12/09` | Intervalo, no campo `since` |

### Enviar exige duas etapas

`send_text` e `send_media` com `confirmar=False` (o padrão) **não enviam nada**: devolvem
uma prévia com a instância, o destino já resolvido, se é grupo, e o conteúdo. Só a
repetição com `confirmar=True` dispara.

O destino quase sempre vem de um nome parcial. A prévia é o que impede a mensagem de cair
no grupo errado — e mensagem enviada em grupo de cliente não tem desfazer.

## Limites da API (medidos, não supostos)

> A documentação da uazapi promete algumas coisas que o servidor não entrega. Tudo abaixo
> foi verificado com chamadas reais e testes discriminantes — o raciocínio completo está em
> [`docs/api-uazapi.md`](docs/api-uazapi.md).

1. **Não existe filtro de data no servidor.** `/message/find` ignora `messageTimestamp`,
   `dateStart`/`dateEnd` e variações. O recorte por período é feito no cliente, paginando
   do mais recente para trás: barato para janelas recentes, caro para varrer meses.
2. **`fromMe` e `messageType` filtram server-side** — conferido contra a contagem real do
   chat. Por isso pedir só os áudios é eficiente.
3. **`transcribe: true` do `/message/download` pode não transcrever**: depende de uma chave
   OpenAI configurada no servidor uazapi. Sem ela, devolve só o arquivo, sem erro. Daí a
   transcrição local via Scribe v2.
4. **O `fileURL` da uazapi é público, sem autenticação** — confirmado baixando o arquivo
   sem nenhum token. Este servidor grava a mídia em disco e devolve o caminho; o link nunca
   circula.
5. **A uazapi expurga o histórico antigo** em poucos dias. Para períodos que o
   `get_messages` não alcança, use `sync_history` (exige o celular do dono online).
6. **Mídia antiga expira no WhatsApp** e não volta. O transcript registra o que era.

## Privacidade

Conversa de WhatsApp é dado pessoal de terceiro. Este servidor grava mídias no disco local
e, quando você configura a chave, as transcrições passam pela API da ElevenLabs. Use com a
autorização de quem é dono do número, mantenha a pasta de mídias fora de qualquer
repositório (o `.gitignore` já cobre) e apague o que não precisa mais.

As tools de envio existem, mas este projeto não implementa disparo em massa — a API da
uazapi tem `/sender/*` para isso, e é justamente o tipo de ferramenta que não deve ficar a
uma chamada de distância de um agente autônomo.

Encontrou uma vulnerabilidade? Veja [SECURITY.md](SECURITY.md) — reporte em privado, não
em issue pública.

## Desenvolvimento

```bash
git clone https://github.com/illumi-ai/uazapi-mcp && cd uazapi-mcp
cp .env.example .env    # preencha
uv sync
uv run --group dev pytest              # testes, sem rede
uv run --group dev ruff check src tests
uv run --env-file .env uazapi-mcp      # servidor em stdio
```

Apontar o Claude Code para o clone local:

```bash
claude mcp add uazapi -- uv run --env-file /caminho/para/uazapi-mcp/.env --directory /caminho/para/uazapi-mcp uazapi-mcp
```

Contribuições e processo de release: [CONTRIBUTING.md](CONTRIBUTING.md) · Histórico:
[CHANGELOG.md](CHANGELOG.md) · Instruções para agentes: [CLAUDE.md](CLAUDE.md)

## Licença

MIT — veja [LICENSE](LICENSE). Projeto independente, sem vínculo com a uazapi ou com o
WhatsApp.
