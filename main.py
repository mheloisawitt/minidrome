"""Ponto de entrada: cria as dependências e conecta as camadas.

Funciona como a raiz de composição (o papel do pacote cmd/ e do Google
Wire no Navidrome): é o único lugar que conhece as implementações concretas.

Configuração por variáveis de ambiente:
    MINIDROME_PASTA    pasta de músicas (padrão: ./musicas)
    MINIDROME_BANCO    arquivo SQLite (padrão: minidrome.db)
    MINIDROME_SEGREDO  segredo para assinar tokens (obrigatório, 16+ caracteres)
    MINIDROME_PORTA    porta HTTP (padrão: 4533)

Criar usuário:  python main.py criar-usuario <nome> <senha>
Iniciar:        python main.py
"""
import os
import sys

from adapters.tags import criar_leitor
from core.autenticacao import ServicoAutenticacao
from core.biblioteca import ServicoBiblioteca
from core.streaming import ServicoStreaming
from core.varredura import ServicoVarredura
from persistence.sqlite import BancoDeDados, SqliteMusicaRepository, SqliteUsuarioRepository
from server.app import Servicos, criar_app


def montar(pasta: str, banco_caminho: str, segredo: str) -> Servicos:
    banco = BancoDeDados(banco_caminho)
    musicas = SqliteMusicaRepository(banco)
    usuarios = SqliteUsuarioRepository(banco)
    return Servicos(
        autenticacao=ServicoAutenticacao(usuarios, segredo),
        biblioteca=ServicoBiblioteca(musicas),
        streaming=ServicoStreaming(musicas, pasta),
        varredura=ServicoVarredura(musicas, criar_leitor(), pasta),
    )


def principal(argv: list[str]) -> None:
    segredo = os.environ.get("MINIDROME_SEGREDO")
    if not segredo:
        sys.exit("Defina a variável MINIDROME_SEGREDO (pelo menos 16 caracteres).")
    servicos = montar(
        pasta=os.environ.get("MINIDROME_PASTA", "musicas"),
        banco_caminho=os.environ.get("MINIDROME_BANCO", "minidrome.db"),
        segredo=segredo,
    )

    if len(argv) == 3 and argv[0] == "criar-usuario":
        servicos.autenticacao.criar_usuario(argv[1], argv[2])
        print(f"Usuário '{argv[1]}' criado.")
        return

    print("Varredura inicial:", servicos.varredura.executar())
    criar_app(servicos).run(host="0.0.0.0", port=int(os.environ.get("MINIDROME_PORTA", "4533")))


if __name__ == "__main__":
    principal(sys.argv[1:])
