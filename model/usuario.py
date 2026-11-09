from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Usuario:
    nome: str
    senha_hash: str  # nunca armazenamos a senha em texto puro


class UsuarioRepository(ABC):
    @abstractmethod
    def buscar(self, nome: str) -> Usuario | None: ...

    @abstractmethod
    def salvar(self, usuario: Usuario) -> None: ...
