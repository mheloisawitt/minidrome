import os

from model.musica import MusicaRepository


class MusicaNaoEncontrada(Exception):
    pass


class ServicoStreaming:
    def __init__(self, repositorio: MusicaRepository, pasta: str):
        self._repositorio = repositorio
        self._pasta = os.path.abspath(pasta)

    def obter_arquivo(self, id: str) -> str:
        """Devolve o caminho absoluto do arquivo, garantindo que ele está na pasta de músicas."""
        musica = self._repositorio.buscar(id)
        if musica is None:
            raise MusicaNaoEncontrada(id)
        caminho = os.path.abspath(os.path.join(self._pasta, musica.caminho))
        # Segurança: impede acesso a arquivos fora da pasta configurada
        if os.path.commonpath([caminho, self._pasta]) != self._pasta or not os.path.isfile(caminho):
            raise MusicaNaoEncontrada(id)
        return caminho
