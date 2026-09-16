"""Download e transcricao das midias das mensagens.

Motivo de existir: o fluxo manual (baixar audio -> mover para pasta -> rodar skill)
e o gargalo. Aqui o audio volta como TEXTO e a imagem como caminho local pronto
para o Read. O fileURL da uazapi e publico sem autenticacao, entao nada de link:
o arquivo e gravado em disco e so o caminho circula.
"""
from __future__ import annotations

import asyncio
import mimetypes
import re
from pathlib import Path
from typing import Any

import certifi
import httpx

from . import config
from .uazapi import baixar_arquivo, baixar_midia

TIPOS_AUDIO = {"AudioMessage", "PttMessage", "VoiceMessage"}
TIPOS_IMAGEM = {"ImageMessage", "StickerMessage"}
TIPOS_VIDEO = {"VideoMessage", "PtvMessage"}
TIPOS_DOC = {"DocumentMessage"}
TIPOS_MIDIA = TIPOS_AUDIO | TIPOS_IMAGEM | TIPOS_VIDEO | TIPOS_DOC | {"AlbumMessage"}

_cache_transcricao: dict[str, str] = {}


def _slug(texto: str, limite: int = 40) -> str:
    s = re.sub(r"[^\w\s-]", "", str(texto), flags=re.UNICODE).strip().replace(" ", "-")
    return (re.sub(r"-+", "-", s)[:limite] or "chat").lower()


def pasta_do_chat(instancia: str, chat_nome: str) -> Path:
    p = config.MEDIA_DIR / _slug(instancia, 30) / _slug(chat_nome)
    p.mkdir(parents=True, exist_ok=True)
    return p


async def transcrever(caminho: Path) -> str:
    """Transcreve um audio com ElevenLabs Scribe v2.

    A uazapi tem `transcribe: true` no /message/download, mas o servidor nao tem
    chave OpenAI configurada e devolve so o arquivo — testado. Scribe v2 tambem
    acerta mais em pt-BR.
    """
    if not config.ELEVENLABS_API_KEY:
        return "[transcricao indisponivel: ELEVENLABS_API_KEY nao configurada]"
    chave = str(caminho)
    if chave in _cache_transcricao:
        return _cache_transcricao[chave]
    try:
        async with httpx.AsyncClient(verify=certifi.where(), timeout=300.0) as cli:
            with caminho.open("rb") as fh:
                r = await cli.post(
                    "https://api.elevenlabs.io/v1/speech-to-text",
                    headers={"xi-api-key": config.ELEVENLABS_API_KEY},
                    files={"file": (caminho.name, fh, "audio/mpeg")},
                    data={"model_id": "scribe_v2", "language_code": "por"},
                )
            if r.status_code >= 400:
                return f"[falha na transcricao: HTTP {r.status_code} {r.text[:150]}]"
            texto = (r.json().get("text") or "").strip()
    except Exception as e:
        return f"[falha na transcricao: {e}]"
    texto = texto or "[audio sem fala detectada]"
    _cache_transcricao[chave] = texto
    return texto


async def processar_midia(token: str, msg: dict, destino: Path, *,
                          transcrever_audio: bool = True) -> dict[str, Any]:
    """Baixa a midia de uma mensagem e, se for audio, transcreve.

    Devolve {'file': caminho|None, 'transcricao': str|None, 'erro': str|None}.
    """
    tipo = msg.get("messageType", "")
    mid = msg.get("messageid") or msg.get("id") or ""
    saida: dict[str, Any] = {"file": None, "transcricao": None, "erro": None}
    if not mid:
        saida["erro"] = "mensagem sem id"
        return saida
    try:
        r = await baixar_midia(token, mid, mp3=tipo in TIPOS_AUDIO)
    except Exception as e:
        saida["erro"] = f"midia indisponivel ({e})"
        return saida
    url = r.get("fileURL")
    if not url:
        saida["erro"] = r.get("error") or "midia expirada no WhatsApp"
        return saida

    conteudo = msg.get("content") if isinstance(msg.get("content"), dict) else {}
    ext = Path(url).suffix or mimetypes.guess_extension(r.get("mimetype", "") or "") or ".bin"
    nome_original = conteudo.get("fileName") or ""
    base = _slug(Path(nome_original).stem, 30) if nome_original else _slug(tipo.replace("Message", ""), 20)
    arquivo = destino / f"{msg.get('messageTimestamp', 0)}-{base}{ext}"
    try:
        if not arquivo.exists():
            await baixar_arquivo(url, arquivo)
    except Exception as e:
        saida["erro"] = f"falha no download: {e}"
        return saida
    saida["file"] = str(arquivo)
    if tipo in TIPOS_AUDIO and transcrever_audio:
        saida["transcricao"] = await transcrever(arquivo)
    return saida


async def processar_lote(token: str, msgs: list[dict], destino: Path, *,
                         transcrever_audio: bool = True, concorrencia: int = 6) -> dict[str, dict]:
    """Processa varias midias em paralelo. Devolve {messageid: resultado}."""
    sem = asyncio.Semaphore(concorrencia)

    async def uma(m: dict):
        async with sem:
            return m.get("messageid"), await processar_midia(
                token, m, destino, transcrever_audio=transcrever_audio)

    pares = await asyncio.gather(*(uma(m) for m in msgs), return_exceptions=True)
    out: dict[str, dict] = {}
    for p in pares:
        if isinstance(p, Exception):
            continue
        mid, res = p
        if mid:
            out[mid] = res
    return out
