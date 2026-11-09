"""Adaptadores para leitura de metadados (equivalente ao adapters/ do Navidrome).

O núcleo depende apenas da interface LeitorDeTags. Trocar a biblioteca
usada aqui não exige nenhuma alteração em core/ ou server/.
"""
import os

from model.musica import LeitorDeTags, Tags


class LeitorNomeDeArquivo(LeitorDeTags):
    """Deduz os metadados da estrutura de pastas: Artista/Álbum/Título.ext"""

    def ler(self, caminho: str) -> Tags:
        partes = os.path.normpath(caminho).split(os.sep)
        titulo = os.path.splitext(partes[-1])[0]
        album = partes[-2] if len(partes) >= 2 else "Desconhecido"
        artista = partes[-3] if len(partes) >= 3 else "Desconhecido"
        return Tags(titulo=titulo, artista=artista, album=album)


class LeitorMutagen(LeitorDeTags):
    """Lê as tags embutidas no arquivo com a biblioteca mutagen.

    Quando o arquivo não tem tags, usa a estrutura de pastas como alternativa.
    """

    def __init__(self):
        import mutagen  # importado aqui para que o restante funcione sem a biblioteca

        self._mutagen = mutagen
        self._alternativo = LeitorNomeDeArquivo()

    def ler(self, caminho: str) -> Tags:
        padrao = self._alternativo.ler(caminho)
        try:
            arquivo = self._mutagen.File(caminho, easy=True)
        except Exception:
            return padrao
        if arquivo is None:
            return padrao

        def primeira(chave: str, alternativa: str) -> str:
            valores = arquivo.tags.get(chave) if arquivo.tags else None
            return valores[0] if valores else alternativa

        return Tags(
            titulo=primeira("title", padrao.titulo),
            artista=primeira("artist", padrao.artista),
            album=primeira("album", padrao.album),
            duracao=int(getattr(arquivo.info, "length", 0) or 0),
        )


def criar_leitor() -> LeitorDeTags:
    try:
        return LeitorMutagen()
    except ImportError:
        return LeitorNomeDeArquivo()
