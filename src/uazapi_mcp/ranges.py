"""Interpreta janelas de tempo em linguagem natural para timestamps em ms.

A uazapi nao filtra por data no servidor (testado: messageTimestamp/dateStart/dateEnd
sao ignorados por /message/find), entao o recorte e feito no cliente e este modulo
define as bordas da janela.
"""
import re
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=-3))  # America/Sao_Paulo


def agora() -> datetime:
    return datetime.now(TZ)


def _inicio_do_dia(d: datetime) -> datetime:
    return d.replace(hour=0, minute=0, second=0, microsecond=0)


def _ms(d: datetime) -> int:
    return int(d.timestamp() * 1000)


def fmt(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, TZ).strftime("%d/%m/%Y %H:%M")


def fmt_dia(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, TZ).strftime("%d/%m/%Y")


_RELATIVO = re.compile(r"^(\d+)\s*(m|min|minutos?|h|horas?|d|dias?|s|semanas?|meses?)$", re.I)
_DATA = re.compile(r"^(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?(?:\s+(\d{1,2}):(\d{2}))?$")
_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2}))?$")


def parse_momento(texto: str, fim_do_dia: bool = False) -> int | None:
    """Converte uma expressao de tempo em timestamp (ms). None = sem limite.

    Aceita: hoje, ontem, anteontem, agora, "3d", "2h", "30min", "1 semana",
    "10/09", "10/09/2026", "10/09 14:30", "2026-09-10", "2026-09-10 14:30".
    """
    if texto is None:
        return None
    t = str(texto).strip().lower()
    if not t or t in ("sempre", "tudo", "todos", "all", "none"):
        return None

    hoje = _inicio_do_dia(agora())
    if t == "agora":
        return _ms(agora())
    if t == "hoje":
        return _ms(hoje + timedelta(days=1) - timedelta(milliseconds=1)) if fim_do_dia else _ms(hoje)
    if t == "ontem":
        base = hoje - timedelta(days=1)
        return _ms(base + timedelta(days=1) - timedelta(milliseconds=1)) if fim_do_dia else _ms(base)
    if t == "anteontem":
        base = hoje - timedelta(days=2)
        return _ms(base + timedelta(days=1) - timedelta(milliseconds=1)) if fim_do_dia else _ms(base)
    if t in ("semana", "esta semana", "essa semana"):
        return _ms(hoje - timedelta(days=hoje.weekday()))
    if t in ("mes", "este mes", "esse mes"):
        return _ms(hoje.replace(day=1))

    m = _RELATIVO.match(t.replace("ultimos ", "").replace("ultimas ", "").strip())
    if m:
        n, unidade = int(m.group(1)), m.group(2).lower()
        if unidade.startswith(("m", "min")) and not unidade.startswith("mes"):
            delta = timedelta(minutes=n)
        elif unidade.startswith("h"):
            delta = timedelta(hours=n)
        elif unidade.startswith("d"):
            delta = timedelta(days=n)
        elif unidade.startswith("s"):
            delta = timedelta(weeks=n)
        else:
            delta = timedelta(days=30 * n)
        return _ms(agora() - delta)

    m = _ISO.match(t)
    if m:
        ano, mes, dia = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh, mm = (int(m.group(4)), int(m.group(5))) if m.group(4) else ((23, 59) if fim_do_dia else (0, 0))
        return _ms(datetime(ano, mes, dia, hh, mm, tzinfo=TZ))

    m = _DATA.match(t)
    if m:
        dia, mes = int(m.group(1)), int(m.group(2))
        ano = int(m.group(3) or agora().year)
        if ano < 100:
            ano += 2000
        hh, mm = (int(m.group(4)), int(m.group(5))) if m.group(4) else ((23, 59) if fim_do_dia else (0, 0))
        return _ms(datetime(ano, mes, dia, hh, mm, tzinfo=TZ))

    raise ValueError(
        f"Nao entendi a data {texto!r}. Use: hoje, ontem, '3d', '2h', '10/09', "
        "'10/09 14:30', '2026-09-10' ou deixe vazio."
    )


def janela(since: str | None, until: str | None) -> tuple[int | None, int | None]:
    """Resolve o par (inicio, fim) em ms. Aceita 'since' no formato '10/09..12/09'."""
    if since and ".." in str(since):
        a, b = str(since).split("..", 1)
        return parse_momento(a.strip()), parse_momento(b.strip(), fim_do_dia=True)
    return parse_momento(since), parse_momento(until, fim_do_dia=True)
