"""Cliente da API uazapi.

Autenticacao por header: `token` (instância) ou `admintoken` (servidor).
O admintoken só e usado para listar instâncias e resolver o token de uma instância
pelo nome; toda leitura e envio usa o token da instância.
"""
from __future__ import annotations

import asyncio
import ssl
import time
from typing import Any

import certifi
import httpx

from . import config

_CTX = ssl.create_default_context(cafile=certifi.where())
_cache_instancias: list[dict[str, Any]] = []
_cache_instancias_em = 0.0
CACHE_INSTANCIAS_SEG = 120


class UazapiError(RuntimeError):
    pass


async def _request(method: str, path: str, body: dict | None = None, *,
                   token: str | None = None, admin: bool = False,
                   timeout: float = 90.0, tentativas: int = 3) -> Any:
    headers = {"Content-Type": "application/json"}
    if admin:
        if not config.ADMIN_TOKEN:
            raise UazapiError("UAZAPI_ADMIN_TOKEN não configurado (variável de ambiente ou ~/.uazapi-mcp/.env).")
        headers["admintoken"] = config.ADMIN_TOKEN
    else:
        if not token:
            raise UazapiError("Token da instância ausente: informe `instance` na chamada.")
        headers["token"] = token

    config.checar_servidor()
    url = f"{config.SERVER}{path}"
    ultimo: Exception | None = None
    for tentativa in range(tentativas):
        try:
            async with httpx.AsyncClient(verify=_CTX, timeout=timeout) as cli:
                r = await cli.request(method, url, json=body, headers=headers)
            if 400 <= r.status_code < 500:
                # Erro de uso (payload, token, âncora ausente): repetir não ajuda.
                raise UazapiError(f"HTTP {r.status_code} em {path}: {r.text[:300]}")
            r.raise_for_status()
            return r.json() if r.content else {}
        except UazapiError:
            raise
        except Exception as e:  # rede, 5xx, timeout
            ultimo = e
            if tentativa == tentativas - 1:
                break
            await asyncio.sleep(2 * (tentativa + 1))
    raise UazapiError(f"Falha em {path} após {tentativas} tentativas: {ultimo}")


async def post(path: str, body: dict, token: str) -> Any:
    return await _request("POST", path, body, token=token)


async def get(path: str, token: str) -> Any:
    return await _request("GET", path, token=token)


# ---------------------------------------------------------------- instâncias

async def listar_instancias(forcar: bool = False) -> list[dict[str, Any]]:
    """Lista as instâncias do servidor. Exige admintoken."""
    global _cache_instancias, _cache_instancias_em
    if _cache_instancias and not forcar and time.monotonic() - _cache_instancias_em < CACHE_INSTANCIAS_SEG:
        return _cache_instancias
    if not config.ADMIN_TOKEN:
        if config.INSTANCE_TOKEN:
            # Conta sem admintoken: dá para operar com o token de uma única instância.
            return [{"name": "(UAZAPI_TOKEN)", "token": config.INSTANCE_TOKEN,
                     "status": "connected", "owner": "", "profileName": ""}]
        raise UazapiError(
            "Defina UAZAPI_ADMIN_TOKEN (token de administrador do servidor) para listar "
            "instâncias, ou UAZAPI_TOKEN para operar com uma instância única.")
    d = await _request("GET", "/instance/all", admin=True)
    _cache_instancias = d if isinstance(d, list) else (d.get("instances") or d.get("data") or [])
    _cache_instancias_em = time.monotonic()
    return _cache_instancias


async def resolver_instancia(instancia: str | None) -> tuple[str, str]:
    """Aceita nome, número (owner) ou o próprio token. Devolve (nome, token).

    Sem argumento, usa UAZAPI_DEFAULT_INSTANCE; se também vazio e houver exatamente
    uma instância conectada, usa essa; senão exige escolha explicita.
    """
    alvo = (instancia or config.DEFAULT_INSTANCE or "").strip()
    if not alvo and config.INSTANCE_TOKEN and not config.ADMIN_TOKEN:
        return "(UAZAPI_TOKEN)", config.INSTANCE_TOKEN
    insts = await listar_instancias()

    if alvo:
        por_token = [i for i in insts if i.get("token") == alvo]
        if por_token:
            return por_token[0].get("name") or "?", alvo
        alvo_l = alvo.lower()
        exatas = [i for i in insts if (i.get("name") or "").lower() == alvo_l
                  or (i.get("owner") or "") == alvo.lstrip("+")]
        parciais = exatas or [i for i in insts
                              if alvo_l in (i.get("name") or "").lower()
                              or alvo_l in (i.get("profileName") or "").lower()
                              or alvo.lstrip("+") in (i.get("owner") or "")]
        if not parciais:
            # Pode ser um token de instância que o admin não lista; tenta direto.
            if len(alvo) > 20:
                return "(token informado)", alvo
            conectadas = [i.get("name") for i in insts if i.get("status") == "connected"]
            raise UazapiError(
                f"Instância {alvo!r} não encontrada. Conectadas agora: {', '.join(conectadas) or 'nenhuma'}."
            )
        if len(parciais) > 1 and not exatas:
            nomes = ", ".join(f"{i.get('name')} ({i.get('status')})" for i in parciais[:8])
            raise UazapiError(f"{alvo!r} casa com várias instâncias: {nomes}. Seja mais específico.")
        escolhida = parciais[0]
        return escolhida.get("name") or "?", escolhida.get("token") or ""

    conectadas = [i for i in insts if i.get("status") == "connected"]
    if len(conectadas) == 1:
        return conectadas[0].get("name") or "?", conectadas[0].get("token") or ""
    nomes = ", ".join(f"{i.get('name')!r} ({i.get('owner') or 'sem número'})" for i in conectadas)
    raise UazapiError(
        "Informe `instance`: há várias instâncias conectadas -> " + (nomes or "nenhuma conectada.")
    )


# ---------------------------------------------------------------------- chats

def jid_de(numero: str) -> str:
    """Normaliza número/JID. Grupos terminam em @g.us, individuais em @s.whatsapp.net."""
    n = str(numero).strip()
    if "@" in n:
        return n
    n = "".join(ch for ch in n if ch.isdigit())
    return f"{n}@g.us" if len(n) > 15 else f"{n}@s.whatsapp.net"


def nome_do_chat(c: dict) -> str:
    return (c.get("wa_contactName") or c.get("name") or c.get("wa_name")
            or c.get("lead_name") or (c.get("wa_chatid") or "").split("@")[0])


async def buscar_chats(token: str, *, busca: str | None = None, tipo: str = "all",
                       limite: int = 30, offset: int = 0) -> list[dict]:
    body: dict[str, Any] = {"limit": min(limite, 100), "offset": offset,
                            "sort": "-wa_lastMsgTimestamp"}
    if tipo == "group":
        body["wa_isGroup"] = True
    elif tipo in ("dm", "individual", "direct"):
        body["wa_isGroup"] = False
    if busca:
        body["operator"] = "OR"
        body["wa_contactName"] = f"~{busca}"
        body["wa_name"] = f"~{busca}"
        body["name"] = f"~{busca}"
    d = await post("/chat/find", body, token)
    return d.get("chats", [])


async def resolver_chat(token: str, chat: str) -> dict:
    """Aceita JID, número ou nome. Devolve o dict do chat (com wa_chatid)."""
    alvo = str(chat).strip()
    if "@" in alvo or alvo.replace("+", "").replace(" ", "").replace("-", "").isdigit():
        jid = jid_de(alvo)
        d = await post("/chat/find", {"wa_chatid": jid, "limit": 1}, token)
        achados = d.get("chats", [])
        if achados:
            return achados[0]
        return {"wa_chatid": jid, "name": alvo, "wa_isGroup": jid.endswith("@g.us")}

    achados = await buscar_chats(token, busca=alvo, limite=20)
    if not achados:
        raise UazapiError(f"Nenhum chat encontrado com {alvo!r}. Use list_chats para procurar.")
    exatos = [c for c in achados if nome_do_chat(c).lower() == alvo.lower()]
    if exatos:
        return exatos[0]
    if len(achados) > 1:
        opcoes = "\n".join(
            f"  - {nome_do_chat(c)} ({'grupo' if c.get('wa_isGroup') else c.get('wa_chatid','').split('@')[0]})"
            for c in achados[:10])
        raise UazapiError(f"{alvo!r} casa com vários chats. Escolha um e repita com o nome exato ou o número:\n{opcoes}")
    return achados[0]


# ------------------------------------------------------------------ mensagens

async def buscar_mensagens(token: str, chatid: str, *, limite: int, offset: int = 0,
                           from_me: bool | None = None, tipo: str | None = None) -> dict:
    body: dict[str, Any] = {"chatid": chatid, "limit": limite, "offset": offset,
                            "sort": "-messageTimestamp"}
    if from_me is not None:
        body["fromMe"] = from_me
    if tipo:
        body["messageType"] = tipo
    return await post("/message/find", body, token)


async def baixar_midia(token: str, message_id: str, *, mp3: bool = True) -> dict:
    return await post("/message/download",
                      {"id": message_id, "return_link": True, "generate_mp3": mp3}, token)


async def baixar_arquivo(url: str, destino) -> int:
    async with httpx.AsyncClient(verify=_CTX, timeout=180.0, follow_redirects=True) as cli:
        r = await cli.get(url)
        r.raise_for_status()
        destino.write_bytes(r.content)
        return len(r.content)
