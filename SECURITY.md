# Segurança

## Como reportar

Encontrou uma vulnerabilidade? **Não abra issue pública.** Use o canal privado do GitHub:

https://github.com/illumi-ai/uazapi-mcp/security/advisories/new

Descreva o cenário, o impacto e, se puder, como reproduzir. Respondemos por lá e o
advisory só vira público depois da correção.

## O que conta como vulnerabilidade aqui

- Qualquer caminho em que o `UAZAPI_ADMIN_TOKEN`, o `UAZAPI_TOKEN` ou a `ELEVENLABS_API_KEY`
  saiam do processo para um destino que não seja o servidor uazapi configurado ou a API da
  ElevenLabs — por exemplo, um arquivo de configuração alheio que consiga redirecionar
  `UAZAPI_SERVER`.
- Escrita fora da pasta de mídias (`UAZAPI_MCP_MEDIA_DIR`) a partir de nomes de chat,
  instância ou arquivo vindos da API.
- Envio de mensagem sem a etapa de confirmação (`confirmar=True`).
- Exposição de tokens em erros, logs ou na saída de `check_config`.

## O que está fora do escopo deste projeto

- O `fileURL` que a uazapi devolve em `/message/download` é acessível sem autenticação.
  Isso é comportamento do servidor uazapi, não deste código. Aqui o link nunca circula: a
  mídia é gravada em disco e só o caminho local aparece. Se isso preocupa, reporte à uazapi.
- Conteúdo das conversas: é dado pessoal de terceiros que passa pelo seu disco e, quando
  você configura a chave, pela ElevenLabs. Use com autorização do dono do número.

## Versões suportadas

Só a release mais recente recebe correções. Fixe a versão pela tag
(`git+https://github.com/illumi-ai/uazapi-mcp@vX.Y.Z`) e acompanhe o
[CHANGELOG](CHANGELOG.md).

## Boas práticas para quem instala

- Prefira passar as credenciais pelo cliente MCP (`claude mcp add --env ...`). Se usar
  arquivo, `~/.uazapi-mcp/.env` com permissão `600`.
- O `UAZAPI_ADMIN_TOKEN` dá acesso a todas as instâncias do servidor. Se você só precisa
  de um número, use o `UAZAPI_TOKEN` daquela instância.
- Apague a pasta de mídias quando não precisar mais dos arquivos.
