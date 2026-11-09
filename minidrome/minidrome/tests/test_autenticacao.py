import pytest

from core.autenticacao import CredenciaisInvalidas, ServicoAutenticacao, verificar_hash
from persistence.sqlite import BancoDeDados, SqliteUsuarioRepository

SEGREDO = "segredo-de-teste-123456"


@pytest.fixture
def auth():
    return ServicoAutenticacao(SqliteUsuarioRepository(BancoDeDados()), SEGREDO)


def test_senha_nao_e_armazenada_em_texto_puro(auth):
    usuario = auth.criar_usuario("ana", "senha-forte-1")
    assert "senha-forte-1" not in usuario.senha_hash
    assert verificar_hash("senha-forte-1", usuario.senha_hash)


def test_login_valido_gera_token_que_identifica_o_usuario(auth):
    auth.criar_usuario("ana", "senha-forte-1")
    assert auth.validar_token(auth.login("ana", "senha-forte-1")) == "ana"


@pytest.mark.parametrize("nome, senha", [("ana", "errada123"), ("ninguem", "senha-forte-1")])
def test_login_invalido_e_recusado(auth, nome, senha):
    auth.criar_usuario("ana", "senha-forte-1")
    with pytest.raises(CredenciaisInvalidas):
        auth.login(nome, senha)


def test_token_adulterado_e_recusado(auth):
    auth.criar_usuario("ana", "senha-forte-1")
    token = auth.login("ana", "senha-forte-1")
    with pytest.raises(CredenciaisInvalidas):
        auth.validar_token(token[:-1] + ("0" if token[-1] != "0" else "1"))


def test_token_expirado_e_recusado():
    auth = ServicoAutenticacao(SqliteUsuarioRepository(BancoDeDados()), SEGREDO, validade_s=-1)
    auth.criar_usuario("ana", "senha-forte-1")
    with pytest.raises(CredenciaisInvalidas):
        auth.validar_token(auth.login("ana", "senha-forte-1"))


def test_senha_curta_e_recusada(auth):
    with pytest.raises(ValueError):
        auth.criar_usuario("ana", "123")
