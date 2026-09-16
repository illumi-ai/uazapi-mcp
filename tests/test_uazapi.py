"""Testes das funcoes puras do cliente (sem rede)."""
import pytest

from uazapi_mcp.uazapi import jid_de, nome_do_chat


@pytest.mark.parametrize("entrada,esperado", [
    ("5511999990000", "5511999990000@s.whatsapp.net"),
    ("+55 11 99999-0000", "5511999990000@s.whatsapp.net"),
    ("5521988880000@s.whatsapp.net", "5521988880000@s.whatsapp.net"),
    ("120363000000000001", "120363000000000001@g.us"),
    ("120363000000000001@g.us", "120363000000000001@g.us"),
])
def test_jid_de(entrada, esperado):
    assert jid_de(entrada) == esperado


def test_nome_do_chat_prefere_contato_salvo():
    assert nome_do_chat({"wa_contactName": "Cliente X", "name": "outro"}) == "Cliente X"


def test_nome_do_chat_cai_para_o_numero():
    assert nome_do_chat({"wa_chatid": "5511999990000@s.whatsapp.net"}) == "5511999990000"
