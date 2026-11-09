"""Testes de ponta a ponta da API: protegem o contrato usado pelos clientes."""


def autenticado(token):
    return {"Authorization": f"Bearer {token}"}


def test_saude_nao_exige_login(cliente):
    assert cliente.get("/api/saude").status_code == 200


def test_rotas_protegidas_exigem_token(cliente):
    for rota in ["/api/albuns", "/api/musicas?q=te", "/api/musicas/x/stream"]:
        assert cliente.get(rota).status_code == 401


def test_login_com_senha_errada(cliente):
    resposta = cliente.post("/api/login", json={"usuario": "heloisa", "senha": "errada"})
    assert resposta.status_code == 401


def test_lista_albuns(cliente, token):
    albuns = cliente.get("/api/albuns", headers=autenticado(token)).get_json()
    assert {"nome": "Dois", "artista": "Legião Urbana", "total_musicas": 2} in albuns
    assert len(albuns) == 2


def test_pesquisa_nao_expoe_caminho_do_arquivo(cliente, token):
    [musica] = cliente.get("/api/musicas?q=Máscara", headers=autenticado(token)).get_json()
    assert musica["artista"] == "Pitty"
    assert "caminho" not in musica


def test_pesquisa_curta_e_recusada(cliente, token):
    assert cliente.get("/api/musicas?q=a", headers=autenticado(token)).status_code == 400


def test_stream_devolve_o_arquivo(cliente, token):
    [musica] = cliente.get("/api/musicas?q=Tempo", headers=autenticado(token)).get_json()
    resposta = cliente.get(f"/api/musicas/{musica['id']}/stream", headers=autenticado(token))
    assert resposta.status_code == 200
    assert resposta.data == b"ID3-falso-1"


def test_stream_suporta_requisicao_parcial(cliente, token):
    [musica] = cliente.get("/api/musicas?q=Tempo", headers=autenticado(token)).get_json()
    cabecalhos = {**autenticado(token), "Range": "bytes=0-2"}
    resposta = cliente.get(f"/api/musicas/{musica['id']}/stream", headers=cabecalhos)
    assert resposta.status_code == 206
    assert resposta.data == b"ID3"


def test_stream_de_musica_inexistente(cliente, token):
    assert cliente.get("/api/musicas/naoexiste/stream", headers=autenticado(token)).status_code == 404


def test_token_por_parametro_para_players(cliente, token):
    """Players de áudio nem sempre enviam cabeçalhos; o token pode ir na URL."""
    [musica] = cliente.get("/api/musicas?q=Tempo", headers=autenticado(token)).get_json()
    assert cliente.get(f"/api/musicas/{musica['id']}/stream?token={token}").status_code == 200
