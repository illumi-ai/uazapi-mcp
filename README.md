# uazapi-mcp

Servidor MCP para ler, transcrever e enviar mensagens de **WhatsApp** pela
[uazapi](https://docs.uazapi.com/), direto do Claude Code (ou qualquer cliente MCP).

O ganho principal: **áudio volta como texto e mídia como arquivo local, numa chamada só.**
Em vez de baixar o áudio, mover para uma pasta, rodar uma ferramenta de transcrição e
copiar a imagem na mão, você pede a conversa e recebe tudo pronto para analisar.

```
> o que o cliente falou no grupo Suporte hoje?

[16/09/2026 09:12] Marcos: [audio] transcricao: "Bom dia, o sistema travou na hora de
  emitir a nota, aparece um erro de conexão e não deixa salvar o pedido..."
[16/09/2026 09:14] Marcos: [imagem] arquivo: ~/.uazapi-mcp/media/suporte/1789-print.jpg
[16/09/2026 09:15] NOS: Já estamos olhando, Marcos.
```

## Instalação

Requer [uv](https://docs.astral.sh/uv/) e Python 3.11+. Não precisa clonar: o `uvx` baixa
e roda o pacote direto do repositório.

```bash
claude mcp add uazapi \
  --env UAZAPI_SERVER=https://suaempresa.uazapi.com \
  --env UAZAPI_ADMIN_TOKEN=seu_admin_token \
  --env ELEVENLABS_API_KEY=sua_chave_elevenlabs \
  -- uvx --from git+https://github.com/illumi-ai/uazapi-mcp uazapi-mcp
```

Reinicie a sessão e rode `check_config` para conferir. Para outros clientes MCP
(Claude Desktop, Cursor, etc.), o equivalente em JSON:

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

### Instalar a skill (recomendado)

O repositório traz uma skill que ensina ao agente os fluxos compostos — qual instância
usar, como fechar janelas de tempo, quando pedir histórico e o ritual de confirmação
antes de enviar:

```bash
git clone https://github.com/illumi-ai/uazapi-mcp && cp -r uazapi-mcp/skills/whatsapp ~/.claude/skills/
```

Detalhes em [`skills/README.md`](skills/README.md).

## Configuração

| Variável | Obrigatória | Para que serve |
|---|---|---|
| `UAZAPI_SERVER` | sim | Servidor da sua conta, ex.: `https://suaempresa.uazapi.com` |
| `UAZAPI_ADMIN_TOKEN` | sim¹ | Lista as instâncias e resolve o token de cada uma pelo nome |
| `UAZAPI_TOKEN` | sim¹ | Alternativa: token de **uma** instância, quando você só tem acesso a ela |
| `UAZAPI_DEFAULT_INSTANCE` | não | Instância usada quando a chamada não informa `instance` |
| `ELEVENLABS_API_KEY` | não | Transcrição de áudio (Scribe v2). Sem ela, o áudio é baixado mas não transcrito |
| `UAZAPI_MCP_MEDIA_DIR` | não | Onde gravar as mídias (default `~/.uazapi-mcp/media`) |
| `UAZAPI_MCP_MAX_MENSAGENS`<br>`UAZAPI_MCP_MAX_TRANSCRICOES`<br>`UAZAPI_MCP_MAX_DOWNLOADS` | não | Tetos por chamada: `3000` / `30` / `60` |

¹ Um dos dois. Os tokens saem do painel da uazapi.

As variáveis também podem ficar num `.env` — no diretório de trabalho, em
`~/.uazapi-mcp/.env` ou em `~/.claude/.env` (nessa ordem de precedência, sempre atrás das
variáveis já exportadas). Copie de [`.env.example`](.env.example).

## Tools

### Leitura

| Tool | O que faz |
|---|---|
| `check_config` | Estado da configuração e teste de conexão, sem revelar segredos |
| `list_instances` | Números de WhatsApp disponíveis no servidor e quais estão conectados |
| `list_chats` | Conversas por recência, com busca por nome e filtro grupo/individual |
| `list_groups` | Grupos de que o número participa, com identificador |
| `get_messages` | **Principal.** Conversa numa janela de tempo, áudios transcritos e mídias baixadas |
| `get_media` | Só os arquivos de um período, por tipo (áudio, imagem, vídeo, documento) |
| `search_messages` | Procura um termo nas mensagens recentes |
| `get_chat_info` | Detalhes de um contato ou grupo |
| `sync_history` | Pede ao celular o histórico antigo que a uazapi já expurgou |

### Envio

| Tool | O que faz |
|---|---|
| `send_text` | Envia texto — exige confirmação em duas etapas |
| `send_media` | Envia arquivo local ou URL — exige confirmação em duas etapas |
| `mark_read` | Marca as últimas mensagens recebidas como lidas |
| `react` | Reage a uma mensagem |
| `transcribe_file` | Transcreve um arquivo de áudio local |

Referência completa dos parâmetros em [`docs/tools.md`](docs/tools.md).

### Janelas de tempo

`get_messages`, `get_media` e `search_messages` aceitam datas em linguagem natural:

| Expressão | Significado |
|---|---|
| `hoje`, `ontem`, `anteontem` | O dia inteiro (use `until` igual para fechar) |
| `2h`, `30min`, `3d`, `1 semana` | Contado a partir de agora |
| `semana`, `mes` | Desde o início da semana/mês corrente |
| `10/09`, `10/09/2026`, `10/09 14:30` | Data brasileira, com hora opcional |
| `2026-09-10`, `2026-09-10 14:30` | ISO |
| `10/09..12/09` | Intervalo, no campo `since` |

### Envio em duas etapas

`send_text` e `send_media` com `confirmar=False` (o padrão) **não enviam nada**: devolvem
uma prévia com a instância, o destino já resolvido, se é grupo, e o conteúdo. Só a
repetição da chamada com `confirmar=True` dispara. O destino costuma vir de um nome
parcial — a prévia é o que impede a mensagem de cair no grupo errado.

## Limites da API (medidos, não supostos)

1. **Não há filtro de data no servidor.** `/message/find` ignora `messageTimestamp`,
   `dateStart`/`dateEnd` — testado com janelas discriminantes. O recorte por período é
   feito no cliente, paginando do mais recente para trás: barato para janelas recentes,
   caro para varrer meses.
2. **`fromMe` e `messageType` filtram server-side** (conferido contra a contagem real do
   chat). Por isso `tipo_mensagem="AudioMessage"` é eficiente.
3. **`transcribe: true` do `/message/download` pode não transcrever**: depende de uma
   chave OpenAI configurada no servidor uazapi. Quando não há, devolve só o arquivo — daí
   a transcrição local via Scribe v2.
4. **O `fileURL` devolvido pela uazapi é público, sem autenticação.** Confirmado baixando
   o arquivo sem nenhum token. Este servidor grava a mídia em disco e devolve o caminho;
   o link nunca circula.
5. **A uazapi expurga o histórico antigo** em poucos dias. Para períodos que o
   `get_messages` não alcança, use `sync_history` (exige o celular do dono online) e
   espere cerca de um minuto.
6. **Mídia antiga expira no WhatsApp** e não volta. O transcript registra o que era.

Notas detalhadas em [`docs/api-uazapi.md`](docs/api-uazapi.md).

## Privacidade

Conversas de WhatsApp são dados pessoais de terceiros. Este servidor grava mídias no disco
local (`~/.uazapi-mcp/media` por padrão) e as transcrições passam pela API da ElevenLabs
quando você configura a chave. Use com a autorização de quem é dono do número, mantenha a
pasta de mídias fora de qualquer repositório e apague o que não precisa mais.

## Desenvolvimento

```bash
git clone https://github.com/illumi-ai/uazapi-mcp && cd uazapi-mcp
cp .env.example .env    # preencha
uv sync
uv run --group dev pytest        # 31 testes, sem rede
uv run uazapi-mcp                # roda o servidor em stdio
```

Para apontar o Claude Code para o clone local em vez do GitHub:

```bash
claude mcp add uazapi -- uv run --directory /caminho/para/uazapi-mcp uazapi-mcp
```

## Licença

MIT — veja [LICENSE](LICENSE).
