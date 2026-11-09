"""Varredura da pasta de músicas (equivalente ao pacote scanner/ do Navidrome)."""
import hashlib
import os

from model.musica import LeitorDeTags, Musica, MusicaRepository

EXTENSOES_SUPORTADAS = {".mp3", ".flac", ".ogg", ".opus", ".m4a", ".wav"}


class ServicoVarredura:
    def __init__(self, repositorio: MusicaRepository, leitor: LeitorDeTags, pasta: str):
        self._repositorio = repositorio
        self._leitor = leitor
        self._pasta = os.path.abspath(pasta)

    @staticmethod
    def gerar_id(caminho_relativo: str) -> str:
        """O id é estável: o mesmo arquivo recebe o mesmo id em toda varredura."""
        return hashlib.sha1(caminho_relativo.encode("utf-8")).hexdigest()[:16]

    def executar(self) -> dict[str, int]:
        encontrados: set[str] = set()
        for raiz, _, arquivos in os.walk(self._pasta):
            for nome in sorted(arquivos):
                if os.path.splitext(nome)[1].lower() not in EXTENSOES_SUPORTADAS:
                    continue
                caminho = os.path.join(raiz, nome)
                relativo = os.path.relpath(caminho, self._pasta)
                tags = self._leitor.ler(caminho)
                musica = Musica(
                    id=self.gerar_id(relativo),
                    titulo=tags.titulo,
                    artista=tags.artista,
                    album=tags.album,
                    caminho=relativo,
                    duracao=tags.duracao,
                )
                self._repositorio.salvar(musica)
                encontrados.add(musica.id)
        removidas = self._repositorio.remover_ausentes(encontrados)
        return {"indexadas": len(encontrados), "removidas": removidas}
