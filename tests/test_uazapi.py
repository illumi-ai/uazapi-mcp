"""Testes das funcoes puras do cliente (sem rede)."""
import pytest

from uazapi_mcp.uazapi import jid_de, nome_do_chat


@pytest.mark.parametrize("entrada,esperado", [
    ("556281978999", "556281978999@s.whatsapp.net"),
    ("+55 62 8197-8999", "556281978999@s.whatsapp.net"),
    ("556182421999@s.whatsapp.net", "556182421999@s.whatsapp.net"),
    ("120363408694977208", "120363408694977208@g.us"),
    ("120363408694977208@g.us", "120363408694977208@g.us"),
])
def test_jid_de(entrada, esperado):
    assert jid_de(entrada) == esperado


def test_nome_do_chat_prefere_contato_salvo():
    assert nome_do_chat({"wa_contactName": "Cliente X", "name": "outro"}) == "Cliente X"


def test_nome_do_chat_cai_para_o_numero():
    assert nome_do_chat({"wa_chatid": "556281978999@s.whatsapp.net"}) == "556281978999"
