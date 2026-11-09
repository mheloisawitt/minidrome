"""Autenticação centralizada na camada core.

Senhas são armazenadas com PBKDF2-SHA256 e salt aleatório. Os tokens de
acesso são assinados com HMAC e possuem prazo de validade.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time

from model.usuario import Usuario, UsuarioRepository

ITERACOES = 200_000


class CredenciaisInvalidas(Exception):
    pass


def gerar_hash(senha: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derivada = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, ITERACOES)
    return f"{salt.hex()}${derivada.hex()}"


def verificar_hash(senha: str, senha_hash: str) -> bool:
    salt_hex, _ = senha_hash.split("$", 1)
    return hmac.compare_digest(gerar_hash(senha, bytes.fromhex(salt_hex)), senha_hash)


class ServicoAutenticacao:
    def __init__(self, repositorio: UsuarioRepository, segredo: str, validade_s: int = 3600):
        if len(segredo) < 16:
            raise ValueError("O segredo precisa ter pelo menos 16 caracteres")
        self._repositorio = repositorio
        self._segredo = segredo.encode()
        self._validade = validade_s

    def criar_usuario(self, nome: str, senha: str) -> Usuario:
        if self._repositorio.buscar(nome):
            raise ValueError(f"Usuário '{nome}' já existe")
        if len(senha) < 8:
            raise ValueError("A senha precisa ter pelo menos 8 caracteres")
        usuario = Usuario(nome=nome, senha_hash=gerar_hash(senha))
        self._repositorio.salvar(usuario)
        return usuario

    def login(self, nome: str, senha: str) -> str:
        usuario = self._repositorio.buscar(nome)
        if usuario is None or not verificar_hash(senha, usuario.senha_hash):
            raise CredenciaisInvalidas()
        return self._assinar({"sub": nome, "exp": int(time.time()) + self._validade})

    def validar_token(self, token: str) -> str:
        """Devolve o nome do usuário ou lança CredenciaisInvalidas."""
        try:
            corpo_b64, assinatura = token.split(".", 1)
            esperada = self._assinatura(corpo_b64)
            if not hmac.compare_digest(assinatura, esperada):
                raise CredenciaisInvalidas()
            dados = json.loads(base64.urlsafe_b64decode(corpo_b64))
        except (ValueError, json.JSONDecodeError) as erro:
            raise CredenciaisInvalidas() from erro
        if dados["exp"] < time.time():
            raise CredenciaisInvalidas()
        return dados["sub"]

    def _assinar(self, dados: dict) -> str:
        corpo_b64 = base64.urlsafe_b64encode(json.dumps(dados).encode()).decode()
        return f"{corpo_b64}.{self._assinatura(corpo_b64)}"

    def _assinatura(self, corpo_b64: str) -> str:
        return hmac.new(self._segredo, corpo_b64.encode(), hashlib.sha256).hexdigest()
