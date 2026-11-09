"""Camada de apresentação: rotas HTTP da API REST.

Esta camada só conversa com os serviços do core; ela não acessa o banco
de dados diretamente.
"""
from dataclasses import asdict, dataclass
from functools import wraps

from flask import Flask, g, jsonify, request, send_file

from core.autenticacao import CredenciaisInvalidas, ServicoAutenticacao
from core.biblioteca import ServicoBiblioteca
from core.streaming import MusicaNaoEncontrada, ServicoStreaming
from core.varredura import ServicoVarredura


@dataclass
class Servicos:
    autenticacao: ServicoAutenticacao
    biblioteca: ServicoBiblioteca
    streaming: ServicoStreaming
    varredura: ServicoVarredura


def criar_app(servicos: Servicos) -> Flask:
    app = Flask(__name__)

    def requer_login(rota):
        @wraps(rota)
        def protegida(*args, **kwargs):
            cabecalho = request.headers.get("Authorization", "")
            token = cabecalho.removeprefix("Bearer ").strip() or request.args.get("token", "")
            try:
                g.usuario = servicos.autenticacao.validar_token(token)
            except CredenciaisInvalidas:
                return jsonify(erro="Não autenticado"), 401
            return rota(*args, **kwargs)

        return protegida

    @app.get("/api/saude")
    def saude():
        return jsonify(status="ok")

    @app.post("/api/login")
    def login():
        dados = request.get_json(silent=True) or {}
        try:
            token = servicos.autenticacao.login(dados.get("usuario", ""), dados.get("senha", ""))
        except CredenciaisInvalidas:
            return jsonify(erro="Usuário ou senha inválidos"), 401
        return jsonify(token=token)

    @app.get("/api/albuns")
    @requer_login
    def albuns():
        return jsonify([asdict(a) for a in servicos.biblioteca.listar_albuns()])

    @app.get("/api/musicas")
    @requer_login
    def pesquisar():
        try:
            musicas = servicos.biblioteca.pesquisar(request.args.get("q", ""))
        except ValueError as erro:
            return jsonify(erro=str(erro)), 400
        return jsonify([publica(m) for m in musicas])

    @app.get("/api/musicas/<id>")
    @requer_login
    def detalhar(id):
        musica = servicos.biblioteca.buscar(id)
        if musica is None:
            return jsonify(erro="Música não encontrada"), 404
        return jsonify(publica(musica))

    @app.get("/api/musicas/<id>/stream")
    @requer_login
    def stream(id):
        try:
            caminho = servicos.streaming.obter_arquivo(id)
        except MusicaNaoEncontrada:
            return jsonify(erro="Música não encontrada"), 404
        # conditional=True habilita requisições parciais (Range), usadas pelos players
        return send_file(caminho, conditional=True)

    @app.post("/api/varredura")
    @requer_login
    def varredura():
        return jsonify(servicos.varredura.executar())

    return app


def publica(musica) -> dict:
    """Representação externa: não expõe o caminho do arquivo no servidor."""
    dados = asdict(musica)
    dados.pop("caminho")
    return dados
