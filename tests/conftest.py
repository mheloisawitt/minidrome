import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.tags import LeitorNomeDeArquivo  # noqa: E402
from core.autenticacao import ServicoAutenticacao  # noqa: E402
from core.biblioteca import ServicoBiblioteca  # noqa: E402
from core.streaming import ServicoStreaming  # noqa: E402
from core.varredura import ServicoVarredura  # noqa: E402
from persistence.sqlite import BancoDeDados, SqliteMusicaRepository, SqliteUsuarioRepository  # noqa: E402
from server.app import Servicos, criar_app  # noqa: E402

SEGREDO = "segredo-de-teste-123456"


@pytest.fixture
def pasta_musicas(tmp_path):
    """Cria uma biblioteca falsa no formato Artista/Álbum/Música.mp3"""
    arquivos = {
        "Legião Urbana/Dois/Tempo Perdido.mp3": b"ID3-falso-1",
        "Legião Urbana/Dois/Índios.mp3": b"ID3-falso-2",
        "Pitty/Admirável Chip Novo/Máscara.flac": b"fLaC-falso",
        "notas.txt": b"nao e musica",
    }
    for relativo, conteudo in arquivos.items():
        caminho = tmp_path / relativo
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(conteudo)
    return tmp_path


@pytest.fixture
def repositorio_musicas():
    return SqliteMusicaRepository(BancoDeDados(":memory:"))


@pytest.fixture
def servicos(pasta_musicas):
    banco = BancoDeDados(":memory:")
    musicas = SqliteMusicaRepository(banco)
    s = Servicos(
        autenticacao=ServicoAutenticacao(SqliteUsuarioRepository(banco), SEGREDO),
        biblioteca=ServicoBiblioteca(musicas),
        streaming=ServicoStreaming(musicas, str(pasta_musicas)),
        varredura=ServicoVarredura(musicas, LeitorNomeDeArquivo(), str(pasta_musicas)),
    )
    s.autenticacao.criar_usuario("heloisa", "senha-forte-1")
    s.varredura.executar()
    return s


@pytest.fixture
def cliente(servicos):
    app = criar_app(servicos)
    app.testing = True
    return app.test_client()


@pytest.fixture
def token(cliente):
    resposta = cliente.post("/api/login", json={"usuario": "heloisa", "senha": "senha-forte-1"})
    return resposta.get_json()["token"]
