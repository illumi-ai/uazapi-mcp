"""Formatacao das mensagens para leitura do agente."""
from __future__ import annotations

from typing import Any

from .midia import TIPOS_AUDIO, TIPOS_DOC, TIPOS_IMAGEM, TIPOS_MIDIA, TIPOS_VIDEO
from .ranges import fmt, fmt_dia

TIPOS_TEXTO = {"Conversation", "ExtendedTextMessage", "TextMessage"}

_ROTULO = {
    "ImageMessage": "imagem", "StickerMessage": "sticker", "VideoMessage": "video",
    "PtvMessage": "video-circulo", "AudioMessage": "audio", "PttMessage": "audio",
    "DocumentMessage": "documento", "AlbumMessage": "album", "LocationMessage": "localizacao",
    "ContactMessage": "contato", "ReactionMessage": "reacao", "PollCreationMessage": "enquete",
}


def texto_da_msg(m: dict) -> str:
    c = m.get("content") if isinstance(m.get("content"), dict) else {}
    return (m.get("text") or c.get("caption") or c.get("fileName") or "").strip()


def autor(m: dict, grupo: bool) -> str:
    if m.get("fromMe"):
        nome = m.get("senderName") or "nos"
        return f"NOS ({nome})" if grupo and m.get("senderName") else "NOS"
    nome = m.get("senderName") or m.get("sender") or ""
    if grupo:
        numero = str(m.get("sender") or "").split("@")[0]
        return f"{nome or numero}" + (f" ({numero})" if nome and numero else "")
    return nome or "cliente"


def linha(m: dict, grupo: bool, midias: dict[str, dict] | None = None) -> str:
    midias = midias or {}
    tipo = m.get("messageType", "")
    ts = fmt(m.get("messageTimestamp", 0))
    quem = autor(m, grupo)
    corpo = texto_da_msg(m)
    partes: list[str] = []

    if tipo not in TIPOS_TEXTO:
        partes.append(f"[{_ROTULO.get(tipo, tipo.replace('Message', '').lower())}]")
    if m.get("quoted"):
        partes.append("(respondendo a outra mensagem)")
    if corpo:
        partes.append(corpo)

    info = midias.get(m.get("messageid", ""))
    if info:
        if info.get("transcricao"):
            partes.append(f'transcricao: "{info["transcricao"]}"')
        if info.get("file"):
            partes.append(f"arquivo: {info['file']}")
        if info.get("erro") and not info.get("file"):
            partes.append(f"({info['erro']})")
    elif tipo in TIPOS_MIDIA and not corpo:
        partes.append("(midia nao baixada)")

    return f"[{ts}] {quem}: " + " ".join(p for p in partes if p)


def transcript(chat: dict, msgs: list[dict], *, midias: dict[str, dict] | None = None,
               cabecalho: str = "") -> str:
    from .uazapi import nome_do_chat
    grupo = bool(chat.get("wa_isGroup"))
    nome = nome_do_chat(chat)
    jid = chat.get("wa_chatid", "")
    if not msgs:
        return f"# {nome}\n\nNenhuma mensagem no periodo pedido.\n{cabecalho}"

    L = [f"# {nome} ({'grupo' if grupo else jid.split('@')[0]})", ""]
    if cabecalho:
        L += [cabecalho, ""]
    L += [f"{len(msgs)} mensagens · {fmt(msgs[0]['messageTimestamp'])} -> {fmt(msgs[-1]['messageTimestamp'])}", ""]

    dia_atual = ""
    for m in msgs:
        dia = fmt_dia(m.get("messageTimestamp", 0))
        if dia != dia_atual:
            L += ["", f"## {dia}", ""]
            dia_atual = dia
        L.append(linha(m, grupo, midias))
    return "\n".join(L)


def _esc(texto: str) -> str:
    """Nomes de grupo costumam ter '|' (ex: 'Empresa | Suporte') e quebram a tabela."""
    return str(texto).replace("|", "\\|")


def resumo_chats(chats: list[dict]) -> str:
    from .uazapi import nome_do_chat
    if not chats:
        return "Nenhum chat encontrado."
    L = ["| Chat | Tipo | Identificador | Ultima mensagem |", "|---|---|---|---|"]
    for c in chats:
        tipo = "grupo" if c.get("wa_isGroup") else "individual"
        ident = c.get("wa_chatid", "")
        ident = ident if c.get("wa_isGroup") else ident.split("@")[0]
        ts = c.get("wa_lastMsgTimestamp") or 0
        L.append(f"| {_esc(nome_do_chat(c))} | {tipo} | `{ident}` | {fmt(ts) if ts else '-'} |")
    return "\n".join(L)


def stats(msgs: list[dict]) -> dict[str, Any]:
    from collections import Counter
    return {"total": len(msgs),
            "nossas": sum(1 for m in msgs if m.get("fromMe")),
            "tipos": dict(Counter(m.get("messageType", "?") for m in msgs).most_common())}
