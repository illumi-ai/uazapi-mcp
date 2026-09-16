"""Testes do parser de janelas de tempo — a logica com mais casos de borda."""
from datetime import datetime, timedelta

import pytest

from uazapi_mcp.ranges import TZ, fmt, janela, parse_momento


def _dt(ts_ms: int) -> datetime:
    return datetime.fromtimestamp(ts_ms / 1000, TZ)


def test_hoje_comeca_meia_noite():
    ts = parse_momento("hoje")
    assert _dt(ts).hour == 0 and _dt(ts).minute == 0


def test_hoje_fim_do_dia():
    ts = parse_momento("hoje", fim_do_dia=True)
    assert _dt(ts).hour == 23 and _dt(ts).minute == 59


def test_ontem_e_um_dia_antes_de_hoje():
    assert _dt(parse_momento("hoje")).date() - _dt(parse_momento("ontem")).date() == timedelta(days=1)


def test_anteontem():
    assert _dt(parse_momento("hoje")).date() - _dt(parse_momento("anteontem")).date() == timedelta(days=2)


@pytest.mark.parametrize("expr,delta", [
    ("2h", timedelta(hours=2)),
    ("30min", timedelta(minutes=30)),
    ("3d", timedelta(days=3)),
    ("1 semana", timedelta(weeks=1)),
])
def test_relativos(expr, delta):
    agora = datetime.now(TZ)
    achado = _dt(parse_momento(expr))
    assert abs((agora - delta) - achado) < timedelta(seconds=5)


def test_data_br_sem_ano_usa_ano_corrente():
    d = _dt(parse_momento("10/09"))
    assert (d.day, d.month, d.year) == (10, 9, datetime.now(TZ).year)


def test_data_br_com_hora():
    d = _dt(parse_momento("10/09/2026 14:30"))
    assert (d.day, d.month, d.year, d.hour, d.minute) == (10, 9, 2026, 14, 30)


def test_data_iso():
    d = _dt(parse_momento("2026-09-10"))
    assert (d.day, d.month, d.year) == (10, 9, 2026)


def test_vazio_e_sem_limite():
    assert parse_momento("") is None
    assert parse_momento(None) is None


def test_intervalo_com_duas_barras():
    inicio, fim = janela("10/09..12/09", None)
    assert _dt(inicio).day == 10
    assert _dt(fim).day == 12 and _dt(fim).hour == 23


def test_until_fecha_no_fim_do_dia():
    _, fim = janela("ontem", "ontem")
    assert _dt(fim).hour == 23 and _dt(fim).minute == 59


def test_expressao_invalida_explica_o_formato():
    with pytest.raises(ValueError, match="Nao entendi a data"):
        parse_momento("semana que vem talvez")


def test_fmt_formato_brasileiro():
    assert fmt(parse_momento("10/09/2026 14:30")) == "10/09/2026 14:30"
