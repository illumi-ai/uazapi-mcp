from uazapi_mcp.midia import espera_para_repetir


def test_respeita_retry_after():
    assert espera_para_repetir("2", 0) == 2.0


def test_retry_after_limitado():
    assert espera_para_repetir("120", 0) == 15.0
    assert espera_para_repetir("0", 0) == 0.5


def test_sem_retry_after_cresce_por_tentativa():
    assert [espera_para_repetir(None, t) for t in range(3)] == [2.0, 4.0, 6.0]


def test_retry_after_em_data_usa_padrao():
    assert espera_para_repetir("Wed, 21 Oct 2026 07:28:00 GMT", 1) == 4.0
