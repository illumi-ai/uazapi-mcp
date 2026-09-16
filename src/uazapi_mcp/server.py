"""MCP server: WhatsApp via uazapi.

Leitura (chats, mensagens, midias com audio ja transcrito) e envio com confirmacao
em duas etapas. Multi-instancia: cada chamada escolhe a instancia, ou usa
UAZAPI_DEFAULT_INSTANCE quando definida.
"""
from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from . import config, formato, uazapi
from .midia import TIPOS_AUDIO, TIPOS_MIDIA, pasta_do_chat, processar_lote, transcrever
from .ranges import fmt, janela

mcp = MCPServer(
    "uazapi",
    instructions=(
        "Le e envia mensagens de WhatsApp via uazapi. Audios voltam transcritos e midias "
        "viram arquivos locais. Envio exige duas etapas: chame com confirmar=False, mostre a "
        "previa ao usuario e so repita com confirmar=True apos o aval dele."
    ),
)


def _erro(e: Exception) -> str:
    return f"ERRO: {e}"


async def _ctx(instancia: str | None, chat: str) -> tuple[str, str, dict]:
    nome_inst, token = await uazapi.resolver_instancia(instancia)
    c = await uazapi.resolver_chat(token, chat)
    return nome_inst, token, c


async def _coletar(token: str, chatid: str, *, inicio: int | None, fim: int | None,
                   limite: int, from_me: bool | None = None, tipo: str | None = None) -> list[dict]:
    """Pagina /message/find do mais recente para tras ate cobrir a janela.

    A uazapi nao filtra por data (testado), entao o recorte e feito aqui.
    """
    coletadas: list[dict] = []
    offset = 0
    teto = min(limite, config.MAX_MENSAGENS)
    while len(coletadas) < teto:
        pagina = min(config.PAGINA, teto - len(coletadas) + 50)
        d = await uazapi.buscar_mensagens(token, chatid, limite=pagina, offset=offset,
                                          from_me=from_me, tipo=tipo)
        lote = d.get("messages", [])
        if not lote:
            break
        antigas_demais = False
        for m in lote:
            ts = m.get("messageTimestamp") or 0
            if fim and ts > fim:
                continue
            if inicio and ts < inicio:
                antigas_demais = True
                continue
            coletadas.append(m)
        if antigas_demais or not d.get("hasMore"):
            break
        offset = d.get("nextOffset", offset + len(lote))
    coletadas.sort(key=lambda m: m.get("messageTimestamp") or 0)
    return coletadas[-teto:]


# ------------------------------------------------------------------- leitura

@mcp.tool()
async def check_config() -> str:
    """Mostra o estado da configuracao e testa a conexao com o servidor uazapi.

    Use quando as outras tools falharem: diz o que falta configurar sem revelar segredos.
    """
    L = ["# Configuracao do uazapi-mcp", ""]
    for k, v in config.diagnostico().items():
        L.append(f"- **{k}**: {v}")
    L.append("")
    if not config.SERVER:
        L.append("UAZAPI_SERVER nao definido — nenhuma chamada vai funcionar. "
                 "Configure as variaveis no cliente MCP (veja o README).")
        return "\n".join(L)
    try:
        insts = await uazapi.listar_instancias(forcar=True)
        conectadas = [i for i in insts if i.get("status") == "connected"]
        L.append(f"Conexao OK: {len(insts)} instancias no servidor, {len(conectadas)} conectadas.")
        if conectadas:
            L.append("Conectadas: " + ", ".join(str(i.get("name")) for i in conectadas))
        else:
            L.append("Nenhuma instancia conectada: conecte uma no painel uazapi antes de ler mensagens.")
    except Exception as e:
        L.append(f"Falha ao falar com {config.SERVER}: {e}")
    if not config.ELEVENLABS_API_KEY:
        L.append("")
        L.append("ELEVENLABS_API_KEY ausente: audios serao baixados, mas nao transcritos.")
    return "\n".join(L)


@mcp.tool()
async def list_instances(apenas_conectadas: bool = True) -> str:
    """Lista as instancias (numeros de WhatsApp) disponiveis no servidor uazapi.

    Use para descobrir qual valor passar em `instance` nas outras tools.
    """
    try:
        insts = await uazapi.listar_instancias(forcar=True)
    except Exception as e:
        return _erro(e)
    if apenas_conectadas:
        insts = [i for i in insts if i.get("status") == "connected"]
    if not insts:
        return "Nenhuma instancia conectada. Conecte uma no painel uazapi ou use apenas_conectadas=False."
    L = ["| Instancia | Numero | Perfil | Status |", "|---|---|---|---|"]
    for i in insts:
        L.append(f"| {i.get('name')} | {i.get('owner') or '-'} | {i.get('profileName') or '-'} | {i.get('status')} |")
    return "\n".join(L)


@mcp.tool()
async def list_chats(busca: str = "", tipo: str = "all", limite: int = 30,
                     instance: str = "") -> str:
    """Lista conversas ordenadas pela mais recente.

    busca: parte do nome do contato/grupo (deixe vazio para as mais recentes).
    tipo: 'all', 'group' (so grupos) ou 'dm' (so individuais).
    instance: nome ou numero da instancia; vazio usa a padrao.
    """
    try:
        _, token = await uazapi.resolver_instancia(instance)
        chats = await uazapi.buscar_chats(token, busca=busca or None, tipo=tipo, limite=limite)
        return formato.resumo_chats(chats)
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def list_groups(busca: str = "", limite: int = 50, instance: str = "") -> str:
    """Lista os grupos de que o numero participa, com o identificador de cada um."""
    try:
        _, token = await uazapi.resolver_instancia(instance)
        d = await uazapi.post("/group/list",
                              {"limit": limite, "noParticipants": True, "search": busca or ""}, token)
        grupos = d.get("groups") or []
        if not grupos:
            return "Nenhum grupo encontrado."
        L = ["| Grupo | Identificador | Participantes |", "|---|---|---|"]
        for g in grupos:
            nome = g.get("Name") or g.get("name") or g.get("subject") or "?"
            jid = g.get("JID") or g.get("jid") or g.get("id") or ""
            n = g.get("participantsCount") or len(g.get("Participants") or g.get("participants") or [])
            L.append(f"| {formato._esc(nome)} | `{jid}` | {n or '-'} |")
        return "\n".join(L)
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def get_messages(chat: str, since: str = "", until: str = "", limite: int = 300,
                       transcrever_audios: bool = True, baixar_midias: bool = True,
                       apenas_nossas: bool = False, tipo_mensagem: str = "",
                       instance: str = "") -> str:
    """Le as mensagens de uma conversa em uma janela de tempo, ja com os audios transcritos.

    chat: nome do contato/grupo, numero (5562...) ou identificador completo.
    since/until: 'hoje', 'ontem', '3d', '2h', '10/09', '10/09 14:30', '2026-09-10'.
                 Tambem aceita intervalo em since: '10/09..12/09'. Vazio = mais recentes.
    transcrever_audios: audios voltam como texto (ElevenLabs Scribe v2).
    baixar_midias: imagens/videos/documentos sao gravados em disco e o caminho vem no
                   transcript, pronto para o Read.
    tipo_mensagem: filtra por tipo, ex 'AudioMessage', 'ImageMessage', 'DocumentMessage'.
    """
    try:
        inicio, fim = janela(since or None, until or None)
        nome_inst, token, c = await _ctx(instance, chat)
        chatid = c["wa_chatid"]
        msgs = await _coletar(token, chatid, inicio=inicio, fim=fim, limite=limite,
                              from_me=True if apenas_nossas else None,
                              tipo=tipo_mensagem or None)
        midias: dict[str, dict] = {}
        avisos: list[str] = []
        if msgs and (baixar_midias or transcrever_audios):
            alvo = [m for m in msgs if m.get("messageType") in TIPOS_MIDIA]
            if not baixar_midias:
                alvo = [m for m in alvo if m.get("messageType") in TIPOS_AUDIO]
            if not transcrever_audios:
                alvo = [m for m in alvo if m.get("messageType") not in TIPOS_AUDIO]
            audios = [m for m in alvo if m.get("messageType") in TIPOS_AUDIO]
            if len(audios) > config.MAX_TRANSCRICOES:
                avisos.append(f"{len(audios)} audios no periodo; transcrevi os {config.MAX_TRANSCRICOES} mais recentes.")
                manter = {m["messageid"] for m in audios[-config.MAX_TRANSCRICOES:]}
                alvo = [m for m in alvo if m.get("messageType") not in TIPOS_AUDIO or m["messageid"] in manter]
            if len(alvo) > config.MAX_DOWNLOADS:
                avisos.append(f"{len(alvo)} midias no periodo; baixei as {config.MAX_DOWNLOADS} mais recentes.")
                alvo = alvo[-config.MAX_DOWNLOADS:]
            if alvo:
                destino = pasta_do_chat(nome_inst, uazapi.nome_do_chat(c))
                midias = await processar_lote(token, alvo, destino,
                                              transcrever_audio=transcrever_audios)
        cab = f"Instancia: {nome_inst}"
        if inicio or fim:
            cab += f" · Janela: {fmt(inicio) if inicio else 'inicio'} -> {fmt(fim) if fim else 'agora'}"
        if avisos:
            cab += "\n" + "\n".join(f"AVISO: {a}" for a in avisos)
        return formato.transcript(c, msgs, midias=midias, cabecalho=cab)
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def get_media(chat: str, since: str = "", until: str = "", tipos: str = "all",
                    transcrever_audios: bool = True, limite: int = 40,
                    instance: str = "") -> str:
    """Baixa as midias de uma conversa para disco e devolve os caminhos locais.

    tipos: 'all', 'audio', 'imagem', 'video' ou 'documento'.
    Audios voltam tambem com a transcricao. Use quando precisar dos arquivos em si;
    para ler a conversa inteira prefira get_messages.
    """
    grupos_tipo = {
        "audio": TIPOS_AUDIO,
        "imagem": {"ImageMessage", "StickerMessage"},
        "video": {"VideoMessage", "PtvMessage"},
        "documento": {"DocumentMessage"},
        "all": TIPOS_MIDIA,
    }
    alvo_tipos = grupos_tipo.get(tipos.lower())
    if alvo_tipos is None:
        return f"ERRO: tipos invalido ({tipos}). Use: all, audio, imagem, video ou documento."
    try:
        inicio, fim = janela(since or None, until or None)
        nome_inst, token, c = await _ctx(instance, chat)
        msgs = await _coletar(token, c["wa_chatid"], inicio=inicio, fim=fim,
                              limite=config.MAX_MENSAGENS)
        alvo = [m for m in msgs if m.get("messageType") in alvo_tipos][-min(limite, config.MAX_DOWNLOADS):]
        if not alvo:
            return f"Nenhuma midia do tipo {tipos} nesse periodo em {uazapi.nome_do_chat(c)}."
        destino = pasta_do_chat(nome_inst, uazapi.nome_do_chat(c))
        res = await processar_lote(token, alvo, destino, transcrever_audio=transcrever_audios)
        L = [f"# Midias de {uazapi.nome_do_chat(c)} ({len(alvo)} arquivos)", "",
             f"Pasta: {destino}", ""]
        for m in alvo:
            info = res.get(m.get("messageid"), {})
            quem = formato.autor(m, bool(c.get("wa_isGroup")))
            L.append(f"- [{fmt(m.get('messageTimestamp', 0))}] {quem} · {m.get('messageType')}")
            if info.get("file"):
                L.append(f"  arquivo: {info['file']}")
            if info.get("transcricao"):
                L.append(f'  transcricao: "{info["transcricao"]}"')
            if info.get("erro"):
                L.append(f"  {info['erro']}")
        return "\n".join(L)
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def search_messages(termo: str, chat: str = "", since: str = "7d", limite_chats: int = 15,
                          instance: str = "") -> str:
    """Procura um termo nas mensagens recentes (a uazapi nao busca texto no servidor).

    chat vazio = varre os chats mais recentes; com chat, busca so nele.
    """
    try:
        nome_inst, token = await uazapi.resolver_instancia(instance)
        inicio, fim = janela(since or None, None)
        alvos = [await uazapi.resolver_chat(token, chat)] if chat else \
            await uazapi.buscar_chats(token, limite=limite_chats)
        termo_l = termo.lower()
        achados: list[str] = []
        for c in alvos:
            msgs = await _coletar(token, c["wa_chatid"], inicio=inicio, fim=fim, limite=500)
            grupo = bool(c.get("wa_isGroup"))
            for m in msgs:
                if termo_l in formato.texto_da_msg(m).lower():
                    achados.append(f"- **{uazapi.nome_do_chat(c)}** · {formato.linha(m, grupo)}")
        if not achados:
            return f"Nada com {termo!r} nos ultimos chats desde {since}."
        return f"# {len(achados)} mensagens com {termo!r}\n\n" + "\n".join(achados[:100])
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def get_chat_info(chat: str, instance: str = "") -> str:
    """Detalhes de um contato ou grupo: identificador, nome, se e grupo, ultima mensagem."""
    try:
        nome_inst, token, c = await _ctx(instance, chat)
        d = await uazapi.post("/chat/details", {"number": c["wa_chatid"], "preview": True}, token)
        alvo = d.get("chat") or d if isinstance(d, dict) else {}
        campos = ["wa_chatid", "wa_contactName", "name", "wa_isGroup", "wa_isGroup_admin",
                  "wa_lastMsgTimestamp", "wa_label", "lead_status", "lead_tags",
                  "wa_isBlocked", "wa_archived", "imagePreview", "phone"]
        L = [f"# {uazapi.nome_do_chat(c)}", "", f"Instancia: {nome_inst}", ""]
        for k in campos:
            v = alvo.get(k, c.get(k))
            if v in (None, "", [], {}):
                continue
            if k == "wa_lastMsgTimestamp":
                v = fmt(v)
            L.append(f"- **{k}**: {v}")
        return "\n".join(L)
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def sync_history(chat: str, quantidade: int = 100, instance: str = "") -> str:
    """Pede ao celular o historico antigo de uma conversa (assincrono).

    Use so quando get_messages nao alcanca o periodo pedido: a uazapi guarda uma
    janela curta. Exige o celular online. As mensagens aparecem no get_messages
    depois de alguns segundos/minutos.
    """
    try:
        nome_inst, token, c = await _ctx(instance, chat)
        r = await uazapi.post("/message/history-sync",
                              {"number": c["wa_chatid"], "mode": "history",
                               "count": min(quantidade, 100)}, token)
        return (f"Sync pedido para {uazapi.nome_do_chat(c)} ({nome_inst}): {r}\n"
                "Aguarde ~1 min e rode get_messages de novo. Se voltar HTTP 400, o chat nao tem "
                "mensagem ancora conhecida.")
    except Exception as e:
        return _erro(e)


# --------------------------------------------------------------------- envio

@mcp.tool()
async def send_text(chat: str, texto: str, confirmar: bool = False, responder_id: str = "",
                    instance: str = "") -> str:
    """Envia uma mensagem de texto. Exige confirmacao em duas etapas.

    Chame primeiro com confirmar=False: nada e enviado e volta um preview com o
    destinatario resolvido. MOSTRE esse preview ao usuario e so chame de novo com
    confirmar=True depois que ele aprovar.
    """
    try:
        nome_inst, token, c = await _ctx(instance, chat)
        destino = uazapi.nome_do_chat(c)
        tipo = "GRUPO" if c.get("wa_isGroup") else "individual"
        if not confirmar:
            return (f"PREVIA — nada foi enviado ainda.\n\n"
                    f"- Instancia: {nome_inst}\n- Destino: {destino} ({tipo}) · `{c['wa_chatid']}`\n"
                    f"- Mensagem:\n\n{texto}\n\n"
                    "Confirme com o usuario e repita a chamada com confirmar=True.")
        body: dict[str, Any] = {"number": c["wa_chatid"], "text": texto}
        if responder_id:
            body["replyid"] = responder_id
        r = await uazapi.post("/send/text", body, token)
        mid = r.get("messageid") or r.get("id") or ""
        return f"Enviado para {destino} ({tipo}) pela instancia {nome_inst}. id={mid}"
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def send_media(chat: str, arquivo: str, tipo: str = "document", legenda: str = "",
                     confirmar: bool = False, instance: str = "") -> str:
    """Envia um arquivo local ou URL. Exige confirmacao em duas etapas, como send_text.

    tipo: image, video, document, audio, ptt (audio de voz) ou sticker.
    """
    try:
        nome_inst, token, c = await _ctx(instance, chat)
        destino = uazapi.nome_do_chat(c)
        ehgrupo = "GRUPO" if c.get("wa_isGroup") else "individual"
        origem = arquivo.strip()
        local = Path(origem).expanduser()
        if not origem.lower().startswith(("http://", "https://")) and not local.is_file():
            return f"ERRO: arquivo nao encontrado: {local}"
        if not confirmar:
            tam = f"{local.stat().st_size/1024:.0f} KB" if local.is_file() else "URL remota"
            return (f"PREVIA — nada foi enviado ainda.\n\n"
                    f"- Instancia: {nome_inst}\n- Destino: {destino} ({ehgrupo}) · `{c['wa_chatid']}`\n"
                    f"- Arquivo: {origem} ({tam}) como {tipo}\n- Legenda: {legenda or '(sem legenda)'}\n\n"
                    "Confirme com o usuario e repita a chamada com confirmar=True.")
        if local.is_file():
            dados = base64.b64encode(local.read_bytes()).decode()
            conteudo = f"data:application/octet-stream;base64,{dados}"
        else:
            conteudo = origem
        body: dict[str, Any] = {"number": c["wa_chatid"], "type": tipo, "file": conteudo}
        if legenda:
            body["text"] = legenda
        if local.is_file() and tipo == "document":
            body["docName"] = local.name
        r = await uazapi.post("/send/media", body, token)
        return f"Enviado para {destino} ({ehgrupo}) pela instancia {nome_inst}. id={r.get('messageid') or r.get('id') or ''}"
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def mark_read(chat: str, quantidade: int = 20, instance: str = "") -> str:
    """Marca como lidas as ultimas mensagens recebidas de uma conversa."""
    try:
        nome_inst, token, c = await _ctx(instance, chat)
        d = await uazapi.buscar_mensagens(token, c["wa_chatid"], limite=min(quantidade, 100))
        ids = [m["messageid"] for m in d.get("messages", []) if not m.get("fromMe")]
        if not ids:
            return "Nenhuma mensagem recebida para marcar."
        await uazapi.post("/message/markread", {"id": ids}, token)
        return f"{len(ids)} mensagens marcadas como lidas em {uazapi.nome_do_chat(c)} ({nome_inst})."
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def react(chat: str, message_id: str, emoji: str = "👍", instance: str = "") -> str:
    """Reage a uma mensagem. emoji vazio remove a reacao."""
    try:
        nome_inst, token, c = await _ctx(instance, chat)
        await uazapi.post("/message/react",
                          {"number": c["wa_chatid"], "id": message_id, "text": emoji}, token)
        return f"Reacao {emoji or '(removida)'} aplicada em {uazapi.nome_do_chat(c)}."
    except Exception as e:
        return _erro(e)


@mcp.tool()
async def transcribe_file(caminho: str) -> str:
    """Transcreve um arquivo de audio local (ElevenLabs Scribe v2).

    Util para audios ja baixados por get_media ou vindos de outro lugar.
    """
    p = Path(caminho).expanduser()
    if not p.is_file():
        return f"ERRO: arquivo nao encontrado: {p}"
    return await transcrever(p)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
