"""Testes do nome, da gravação e da transcrição de mídias (sem rede)."""
import asyncio

import pytest

from uazapi_mcp import config, midia, uazapi


def _audio(mid, ts=1792497565000, **kw):
    base = {"messageid": mid, "messageTimestamp": ts, "messageType": "AudioMessage",
            "content": {}}
    base.update(kw)
    return base


@pytest.fixture(autouse=True)
def _cache_limpo():
    midia._cache_transcricao.clear()
    yield
    midia._cache_transcricao.clear()


def test_mensagens_no_mesmo_segundo_ganham_nomes_diferentes():
    # Áudios encaminhados juntos chegam com o mesmo messageTimestamp.
    a = midia.nome_do_arquivo(_audio("3EB04E3A41F3"), ".mp3")
    b = midia.nome_do_arquivo(_audio("3EB0EE55569E"), ".mp3")
    assert a != b


def test_nome_do_arquivo_nao_carrega_caracteres_do_id_cru():
    nome = midia.nome_do_arquivo(_audio("5511999990000:../3EB0/AB"), ".mp3")
    assert nome.endswith(".mp3")
    assert "/" not in nome and ":" not in nome


def test_nome_do_arquivo_mantem_o_nome_original_do_documento():
    msg = _audio("3EB0ABC123", messageType="DocumentMessage",
                 content={"fileName": "Contrato Final.pdf"})
    assert "contrato-final" in midia.nome_do_arquivo(msg, ".pdf")


def test_gravar_atomico_substitui_sem_deixar_temporario(tmp_path):
    destino = tmp_path / "a.mp3"
    uazapi.gravar_atomico(destino, b"primeiro")
    uazapi.gravar_atomico(destino, b"segundo")
    assert destino.read_bytes() == b"segundo"
    assert [p.name for p in tmp_path.iterdir()] == ["a.mp3"]


def test_audio_identico_em_dois_arquivos_e_transcrito_uma_vez(tmp_path, monkeypatch):
    # O mesmo áudio encaminhado duas vezes vira dois arquivos de conteúdo igual.
    a, b = tmp_path / "1-a.mp3", tmp_path / "1-b.mp3"
    a.write_bytes(b"mesmo audio")
    b.write_bytes(b"mesmo audio")
    chamadas = []

    async def scribe_falso(caminho):
        chamadas.append(caminho)
        await asyncio.sleep(0)
        return True, "texto"

    monkeypatch.setattr(config, "ELEVENLABS_API_KEY", "chave-de-teste")
    monkeypatch.setattr(midia, "_chamar_scribe", scribe_falso)

    async def rodar():
        return await asyncio.gather(midia.transcrever(a), midia.transcrever(b))

    assert asyncio.run(rodar()) == ["texto", "texto"]
    assert len(chamadas) == 1


def test_falha_de_transcricao_nao_fica_no_cache(tmp_path, monkeypatch):
    a = tmp_path / "a.mp3"
    a.write_bytes(b"audio")
    respostas = [(False, "[falha na transcrição: HTTP 500]"), (True, "texto")]

    async def scribe_falso(caminho):
        return respostas.pop(0)

    monkeypatch.setattr(config, "ELEVENLABS_API_KEY", "chave-de-teste")
    monkeypatch.setattr(midia, "_chamar_scribe", scribe_falso)

    assert asyncio.run(midia.transcrever(a)).startswith("[falha")
    assert asyncio.run(midia.transcrever(a)) == "texto"
