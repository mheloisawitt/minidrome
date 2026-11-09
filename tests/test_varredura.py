from adapters.tags import LeitorNomeDeArquivo
from core.varredura import ServicoVarredura
from model.musica import LeitorDeTags, Tags


class LeitorFalso(LeitorDeTags):
    """Dublê de teste: mostra que o núcleo funciona com qualquer adaptador."""

    def ler(self, caminho: str) -> Tags:
        return Tags(titulo="T", artista="A", album="B", duracao=42)


def test_indexa_apenas_arquivos_de_audio(pasta_musicas, repositorio_musicas):
    resultado = ServicoVarredura(repositorio_musicas, LeitorNomeDeArquivo(), str(pasta_musicas)).executar()
    assert resultado == {"indexadas": 3, "removidas": 0}


def test_extrai_metadados_pela_estrutura_de_pastas(pasta_musicas, repositorio_musicas):
    ServicoVarredura(repositorio_musicas, LeitorNomeDeArquivo(), str(pasta_musicas)).executar()
    [musica] = repositorio_musicas.pesquisar("Tempo Perdido")
    assert (musica.artista, musica.album) == ("Legião Urbana", "Dois")


def test_id_e_estavel_entre_varreduras(pasta_musicas, repositorio_musicas):
    varredura = ServicoVarredura(repositorio_musicas, LeitorNomeDeArquivo(), str(pasta_musicas))
    varredura.executar()
    ids_antes = {m.id for m in repositorio_musicas.pesquisar("a")}
    varredura.executar()
    assert {m.id for m in repositorio_musicas.pesquisar("a")} == ids_antes


def test_remove_musicas_apagadas_da_pasta(pasta_musicas, repositorio_musicas):
    varredura = ServicoVarredura(repositorio_musicas, LeitorNomeDeArquivo(), str(pasta_musicas))
    varredura.executar()
    (pasta_musicas / "Pitty" / "Admirável Chip Novo" / "Máscara.flac").unlink()
    assert varredura.executar() == {"indexadas": 2, "removidas": 1}


def test_aceita_outro_adaptador_sem_mudar_o_nucleo(pasta_musicas, repositorio_musicas):
    ServicoVarredura(repositorio_musicas, LeitorFalso(), str(pasta_musicas)).executar()
    assert all(m.duracao == 42 for m in repositorio_musicas.pesquisar("T"))
