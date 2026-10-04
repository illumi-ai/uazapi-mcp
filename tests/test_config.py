from uazapi_mcp.config import escolher_provedor


def test_automatico_prefere_elevenlabs():
    assert escolher_provedor("", elevenlabs=True, openrouter=True) == "elevenlabs"


def test_automatico_cai_para_openrouter():
    assert escolher_provedor("", elevenlabs=False, openrouter=True) == "openrouter"


def test_sem_chave_desliga():
    assert escolher_provedor("", elevenlabs=False, openrouter=False) == ""


def test_escolha_explicita_vence():
    assert escolher_provedor(" OpenRouter ", elevenlabs=True, openrouter=True) == "openrouter"


def test_escolha_sem_chave_nao_troca_de_provedor():
    assert escolher_provedor("openrouter", elevenlabs=True, openrouter=False) == ""


def test_desligada_vence_as_chaves():
    assert escolher_provedor("desligada", elevenlabs=True, openrouter=True) == ""


def test_escolha_desconhecida_usa_automatico():
    assert escolher_provedor("whisper", elevenlabs=False, openrouter=True) == "openrouter"
