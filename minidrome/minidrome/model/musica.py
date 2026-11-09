"""Camada de domínio: entidades e interfaces (portas).

Este pacote não depende de nenhum outro pacote do projeto. As camadas
de persistência e de adaptadores implementam as interfaces definidas aqui.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Musica:
    id: str
    titulo: str
    artista: str
    album: str
    caminho: str
    duracao: int = 0  # segundos


@dataclass
class Album:
    nome: str
    artista: str
    total_musicas: int


@dataclass
class Tags:
    """Metadados extraídos de um arquivo de áudio."""

    titulo: str
    artista: str
    album: str
    duracao: int = 0


class MusicaRepository(ABC):
    @abstractmethod
    def buscar(self, id: str) -> Musica | None: ...

    @abstractmethod
    def pesquisar(self, texto: str) -> list[Musica]: ...

    @abstractmethod
    def salvar(self, musica: Musica) -> None: ...

    @abstractmethod
    def listar_albuns(self) -> list[Album]: ...

    @abstractmethod
    def remover_ausentes(self, ids_presentes: set[str]) -> int: ...


class LeitorDeTags(ABC):
    """Porta para bibliotecas externas de leitura de metadados."""

    @abstractmethod
    def ler(self, caminho: str) -> Tags: ...
