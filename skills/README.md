# Skills

Três skills para Claude Code que usam as tools do MCP `uazapi`. Elas ensinam ao agente os
fluxos que as tools sozinhas não descrevem: qual instância usar, como fechar uma janela de
tempo, quando pedir histórico, o que fazer com um print de erro e o ritual de confirmação
antes de enviar mensagem.

| Skill | Para que serve |
|---|---|
| [`whatsapp`](whatsapp/SKILL.md) | Base: ler, buscar, baixar mídia e responder. É a que você quer se for instalar só uma |
| [`entender-problema`](entender-problema/SKILL.md) | Relato espalhado do cliente (áudio + print + texto) vira documento PROBLEMA com timeline, evidências e severidade |
| [`resumo-do-dia`](resumo-do-dia/SKILL.md) | Briefing das conversas: o que chegou, o que está sem resposta, o que precisa de decisão |

## Instalar

```bash
git clone https://github.com/illumi-ai/uazapi-mcp
cd uazapi-mcp

# todas, para o usuário (valem em qualquer projeto)
cp -r skills/whatsapp skills/entender-problema skills/resumo-do-dia ~/.claude/skills/

# ou só uma
cp -r skills/whatsapp ~/.claude/skills/

# ou apenas neste projeto
mkdir -p .claude/skills && cp -r skills/* .claude/skills/
```

Reinicie a sessão. As skills são acionadas sozinhas quando o pedido combina com a
descrição, ou manualmente: `/whatsapp`, `/entender-problema`, `/resumo-do-dia`.

## Adaptar ao seu fluxo

São arquivos Markdown com frontmatter (`name`, `description`) — edite à vontade. Pontos que
costumam pedir ajuste:

- **`entender-problema`**: o formato do documento final e os níveis de severidade. Se você
  usa um tracker específico, troque a seção "Relato para triagem" pelo formato de issue que
  o seu time espera.
- **`resumo-do-dia`**: quais chats entram no briefing, e a separação entre conversa de
  cliente e grupo interno.
- **`whatsapp`**: a regra de confirmação antes de enviar. Não recomendamos afrouxar: o
  destino é resolvido por nome, e mensagem em grupo errado de cliente não tem desfazer.

Em clientes MCP que não suportam skills, use o conteúdo do `SKILL.md` como instrução de
sistema do agente.
