"""Camada de persistência: implementa as interfaces do model usando SQLite."""
import sqlite3
import threading

from model.musica import Album, Musica, MusicaRepository
from model.usuario import Usuario, UsuarioRepository

ESQUEMA = """
CREATE TABLE IF NOT EXISTS musica (
    id      TEXT PRIMARY KEY,
    titulo  TEXT NOT NULL,
    artista TEXT NOT NULL,
    album   TEXT NOT NULL,
    caminho TEXT NOT NULL UNIQUE,
    duracao INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_musica_album ON musica(album, artista);
CREATE TABLE IF NOT EXISTS usuario (
    nome       TEXT PRIMARY KEY,
    senha_hash TEXT NOT NULL
);
"""


class BancoDeDados:
    """Conexão única compartilhada pelos repositórios, protegida por lock."""

    def __init__(self, caminho: str = ":memory:"):
        self.conexao = sqlite3.connect(caminho, check_same_thread=False)
        self.conexao.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.lock:
            self.conexao.executescript(ESQUEMA)


class SqliteMusicaRepository(MusicaRepository):
    def __init__(self, banco: BancoDeDados):
        self._banco = banco

    def buscar(self, id: str) -> Musica | None:
        with self._banco.lock:
            linha = self._banco.conexao.execute("SELECT * FROM musica WHERE id = ?", (id,)).fetchone()
        return Musica(**dict(linha)) if linha else None

    def pesquisar(self, texto: str) -> list[Musica]:
        termo = f"%{texto}%"
        with self._banco.lock:
            linhas = self._banco.conexao.execute(
                "SELECT * FROM musica WHERE titulo LIKE ? OR artista LIKE ? OR album LIKE ? "
                "ORDER BY artista, album, titulo",
                (termo, termo, termo),
            ).fetchall()
        return [Musica(**dict(linha)) for linha in linhas]

    def salvar(self, musica: Musica) -> None:
        with self._banco.lock, self._banco.conexao:
            self._banco.conexao.execute(
                "INSERT INTO musica (id, titulo, artista, album, caminho, duracao) "
                "VALUES (:id, :titulo, :artista, :album, :caminho, :duracao) "
                "ON CONFLICT(id) DO UPDATE SET titulo=excluded.titulo, artista=excluded.artista, "
                "album=excluded.album, caminho=excluded.caminho, duracao=excluded.duracao",
                musica.__dict__,
            )

    def listar_albuns(self) -> list[Album]:
        with self._banco.lock:
            linhas = self._banco.conexao.execute(
                "SELECT album, artista, COUNT(*) AS total FROM musica "
                "GROUP BY album, artista ORDER BY artista, album"
            ).fetchall()
        return [Album(nome=l["album"], artista=l["artista"], total_musicas=l["total"]) for l in linhas]

    def remover_ausentes(self, ids_presentes: set[str]) -> int:
        with self._banco.lock, self._banco.conexao:
            ids_atuais = {l["id"] for l in self._banco.conexao.execute("SELECT id FROM musica")}
            ausentes = ids_atuais - ids_presentes
            self._banco.conexao.executemany("DELETE FROM musica WHERE id = ?", [(i,) for i in ausentes])
        return len(ausentes)


class SqliteUsuarioRepository(UsuarioRepository):
    def __init__(self, banco: BancoDeDados):
        self._banco = banco

    def buscar(self, nome: str) -> Usuario | None:
        with self._banco.lock:
            linha = self._banco.conexao.execute("SELECT * FROM usuario WHERE nome = ?", (nome,)).fetchone()
        return Usuario(**dict(linha)) if linha else None

    def salvar(self, usuario: Usuario) -> None:
        with self._banco.lock, self._banco.conexao:
            self._banco.conexao.execute(
                "INSERT OR REPLACE INTO usuario (nome, senha_hash) VALUES (?, ?)",
                (usuario.nome, usuario.senha_hash),
            )
