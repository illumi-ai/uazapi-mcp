"""Configuracao do servidor.

Ordem de precedencia:
1. variaveis de ambiente ja exportadas (e o que o cliente MCP injeta via `--env`);
2. `.env` no diretorio de trabalho, util em desenvolvimento;
3. `~/.uazapi-mcp/.env`, para configurar uma vez na maquina;
4. `~/.claude/.env`, conveniencia para quem ja guarda chaves ali.

Instalado via `uvx`, o pacote roda de um cache temporario: nao ha `.env` ao lado do
codigo, entao a configuracao normal vem das variaveis do proprio cliente MCP.
"""
from __future__ import annotations

import os
from pathlib import Path

HOME_DIR = Path.home() / ".uazapi-mcp"
_ENV_FILES = [
    Path.cwd() / ".env",
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
MEDIA_DIR = Path(os.environ.get("UAZAPI_MCP_MEDIA_DIR") or (HOME_DIR / "media")).expanduser()

# Limites de seguranca: impedem que uma chamada solta puxe a base inteira.
MAX_MENSAGENS = int(os.environ.get("UAZAPI_MCP_MAX_MENSAGENS", "3000"))
PAGINA = 500
MAX_TRANSCRICOES = int(os.environ.get("UAZAPI_MCP_MAX_TRANSCRICOES", "30"))
MAX_DOWNLOADS = int(os.environ.get("UAZAPI_MCP_MAX_DOWNLOADS", "60"))


def checar_servidor() -> None:
    """Erro util quando o servidor nao foi configurado, em vez de um 404 cru."""
    if not SERVER:
        raise RuntimeError(
            "UAZAPI_SERVER nao configurado. Informe o servidor da sua conta uazapi "
            "(ex.: https://suaempresa.uazapi.com) no cliente MCP:\n"
            "  claude mcp add uazapi --env UAZAPI_SERVER=https://suaempresa.uazapi.com "
            "--env UAZAPI_ADMIN_TOKEN=seu_token -- uvx --from "
            "git+https://github.com/illumi-ai/uazapi-mcp uazapi-mcp"
        )


def diagnostico() -> dict[str, str]:
    """Estado da configuracao, sem revelar segredos."""
    def marca(v: str) -> str:
        return f"definido ({len(v)} caracteres)" if v else "nao definido"

    return {
        "UAZAPI_SERVER": SERVER or "nao definido",
        "UAZAPI_ADMIN_TOKEN": marca(ADMIN_TOKEN),
        "UAZAPI_TOKEN": marca(INSTANCE_TOKEN),
        "UAZAPI_DEFAULT_INSTANCE": DEFAULT_INSTANCE or "nao definido",
        "ELEVENLABS_API_KEY": marca(ELEVENLABS_API_KEY),
        "pasta de midias": str(MEDIA_DIR),
    }
