"""Configuração do servidor.

Ordem de precedencia:
1. variáveis de ambiente já exportadas (é o que o cliente MCP injeta via `--env`);
2. `~/.uazapi-mcp/.env`, para configurar uma vez na máquina;
3. `~/.claude/.env`, conveniência para quem já guarda chaves ali.

O `.env` do diretório de trabalho NÃO é lido de propósito: o cliente MCP inicia o
servidor com o cwd do projeto aberto, e um `.env` alheio não pode redirecionar
UAZAPI_SERVER (e com ele o token) para outro lugar. Em desenvolvimento, use
`uv run --env-file .env uazapi-mcp`.
"""
from __future__ import annotations

import os
from pathlib import Path

HOME_DIR = Path.home() / ".uazapi-mcp"
_ENV_FILES = [
    HOME_DIR / ".env",
    Path.home() / ".claude" / ".env",
]


def _carregar_env() -> None:
    for path in _ENV_FILES:
        try:
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip().removeprefix("export ").strip()
                v = v.strip().strip("'\"")
                if k and v and k not in os.environ:
                    os.environ[k] = v
        except OSError:
            continue


_carregar_env()

SERVER = os.environ.get("UAZAPI_SERVER", "").rstrip("/")
ADMIN_TOKEN = os.environ.get("UAZAPI_ADMIN_TOKEN", "")
INSTANCE_TOKEN = os.environ.get("UAZAPI_TOKEN", "")
DEFAULT_INSTANCE = os.environ.get("UAZAPI_DEFAULT_INSTANCE", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
TRANSCRICAO_MODELO = os.environ.get("UAZAPI_MCP_TRANSCRICAO_MODELO") or "microsoft/mai-transcribe-2"
MEDIA_DIR = Path(os.environ.get("UAZAPI_MCP_MEDIA_DIR") or (HOME_DIR / "media")).expanduser()



def escolher_provedor(escolha: str, *, elevenlabs: bool, openrouter: bool) -> str:
    """Provedor de transcrição: o pedido em UAZAPI_MCP_TRANSCRICAO, senão o primeiro com chave.

    No automático a ElevenLabs vem antes para não mudar quem já a usava. Devolve "" com
    "desligada", quando o provedor escolhido não tem chave ou quando nenhum tem.
    """
    chaves = {"elevenlabs": elevenlabs, "openrouter": openrouter}
    escolha = escolha.strip().lower()
    if escolha == "desligada":
        return ""
    if escolha in chaves:
        return escolha if chaves[escolha] else ""
    return next((p for p, ok in chaves.items() if ok), "")


TRANSCRICAO_PEDIDA = os.environ.get("UAZAPI_MCP_TRANSCRICAO", "").strip().lower()
PROVEDOR_TRANSCRICAO = escolher_provedor(
    TRANSCRICAO_PEDIDA, elevenlabs=bool(ELEVENLABS_API_KEY), openrouter=bool(OPENROUTER_API_KEY))

# Limites de segurança: impedem que uma chamada solta puxe a base inteira.
MAX_MENSAGENS = int(os.environ.get("UAZAPI_MCP_MAX_MENSAGENS", "3000"))
PAGINA = 500
MAX_TRANSCRICOES = int(os.environ.get("UAZAPI_MCP_MAX_TRANSCRICOES", "30"))
MAX_DOWNLOADS = int(os.environ.get("UAZAPI_MCP_MAX_DOWNLOADS", "60"))


def checar_servidor() -> None:
    """Erro útil quando o servidor não foi configurado, em vez de um 404 cru."""
    if not SERVER:
        raise RuntimeError(
            "UAZAPI_SERVER não configurado. Informe o servidor da sua conta uazapi "
            "(ex.: https://suaempresa.uazapi.com) no cliente MCP:\n"
            "  claude mcp add uazapi --env UAZAPI_SERVER=https://suaempresa.uazapi.com "
            "--env UAZAPI_ADMIN_TOKEN=seu_token -- uvx --from "
            "git+https://github.com/illumi-ai/uazapi-mcp uazapi-mcp"
        )


def descricao_transcricao() -> str:
    if PROVEDOR_TRANSCRICAO == "openrouter":
        return f"OpenRouter ({TRANSCRICAO_MODELO})"
    if PROVEDOR_TRANSCRICAO == "elevenlabs":
        return "ElevenLabs Scribe v2"
    return "desligada"


def diagnostico() -> dict[str, str]:
    """Estado da configuração, sem revelar segredos."""
    def marca(v: str) -> str:
        return f"definido ({len(v)} caracteres)" if v else "não definido"

    return {
        "UAZAPI_SERVER": SERVER or "não definido",
        "UAZAPI_ADMIN_TOKEN": marca(ADMIN_TOKEN),
        "UAZAPI_TOKEN": marca(INSTANCE_TOKEN),
        "UAZAPI_DEFAULT_INSTANCE": DEFAULT_INSTANCE or "não definido",
        "ELEVENLABS_API_KEY": marca(ELEVENLABS_API_KEY),
        "OPENROUTER_API_KEY": marca(OPENROUTER_API_KEY),
        "UAZAPI_MCP_TRANSCRICAO": TRANSCRICAO_PEDIDA or "automático",
        "transcrição": descricao_transcricao(),
        "pasta de mídias": str(MEDIA_DIR),
    }
