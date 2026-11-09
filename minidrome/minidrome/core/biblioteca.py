from model.musica import Album, Musica, MusicaRepository


class ServicoBiblioteca:
    def __init__(self, repositorio: MusicaRepository):
        self._repositorio = repositorio

    def listar_albuns(self) -> list[Album]:
        return self._repositorio.listar_albuns()

    def pesquisar(self, texto: str) -> list[Musica]:
        texto = texto.strip()
        if len(texto) < 2:
            raise ValueError("A pesquisa precisa ter pelo menos 2 caracteres")
        return self._repositorio.pesquisar(texto)

    def buscar(self, id: str) -> Musica | None:
        return self._repositorio.buscar(id)
