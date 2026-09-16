# Skill `whatsapp`

A skill ensina ao agente os fluxos compostos que as tools sozinhas nao descrevem: qual
instancia usar, como fechar uma janela de tempo, quando pedir `sync_history`, e o ritual
de confirmacao antes de enviar mensagem.

## Instalar no Claude Code

```bash
# usuario (vale em todos os projetos)
cp -r skills/whatsapp ~/.claude/skills/

# ou apenas neste projeto
mkdir -p .claude/skills && cp -r skills/whatsapp .claude/skills/
```

Reinicie a sessao. A skill e ativada sozinha quando o pedido envolve WhatsApp, ou
manualmente com `/whatsapp`.

## Outros clientes MCP

O arquivo e Markdown com frontmatter (`name`, `description`). Em clientes que nao suportam
skills, use o conteudo de `whatsapp/SKILL.md` como instrucao de sistema do agente.
