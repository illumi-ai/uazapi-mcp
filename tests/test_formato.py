"""Testes da montagem do transcript."""
from uazapi_mcp import formato


def _msg(**kw):
    base = {"messageid": "A1", "messageTimestamp": 1789488899000, "fromMe": False,
            "senderName": "Cliente", "messageType": "Conversation", "text": "oi"}
    base.update(kw)
    return base


def test_linha_de_texto_traz_autor_e_horario():
    linha = formato.linha(_msg(), grupo=False)
    assert "Cliente" in linha and "oi" in linha and "15/09/2026" in linha


def test_nossa_mensagem_aparece_como_nos():
    assert "] NÓS:" in formato.linha(_msg(fromMe=True), grupo=False)


def test_em_grupo_nossa_mensagem_identifica_quem_escreveu():
    linha = formato.linha(_msg(fromMe=True, senderName="Ana"), grupo=True)
    assert "NÓS (Ana)" in linha


def test_audio_mostra_transcricao():
    m = _msg(messageType="AudioMessage", text="")
    linha = formato.linha(m, grupo=False, midias={"A1": {"transcricao": "bom dia", "file": "~/.uazapi-mcp/media/x/a.mp3"}})
    assert "[áudio]" in linha and "bom dia" in linha and "media/x/a.mp3" in linha


def test_midia_expirada_e_sinalizada():
    m = _msg(messageType="ImageMessage", text="")
    linha = formato.linha(m, grupo=False, midias={"A1": {"erro": "mídia expirada no WhatsApp"}})
    assert "expirada" in linha


def test_transcript_agrupa_por_dia():
    out = formato.transcript({"wa_chatid": "1@g.us", "name": "G", "wa_isGroup": True},
                             [_msg(), _msg(messageTimestamp=1789575299000, text="segundo")])
    assert out.count("## ") == 2


def test_transcript_vazio_nao_quebra():
    out = formato.transcript({"wa_chatid": "1@s.whatsapp.net", "name": "X"}, [])
    assert "Nenhuma mensagem" in out


def test_pipe_no_nome_do_grupo_nao_quebra_a_tabela():
    linha = formato.resumo_chats([{"wa_chatid": "1@g.us", "name": "Rec | Branding",
                                   "wa_isGroup": True, "wa_lastMsgTimestamp": 1789488899000}])
    assert r"Rec \| Branding" in linha
