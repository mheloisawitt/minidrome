"""Testes de arquitetura: verificam que as regras de dependência entre camadas são respeitadas.

Regras (seção 6.2 do trabalho):
- model não depende de nenhum outro pacote do projeto;
- core depende apenas de model;
- server não acessa persistence nem adapters diretamente.
"""
import ast
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PACOTES = {"model", "core", "persistence", "adapters", "server"}

PROIBIDOS = {
    "model": {"core", "persistence", "adapters", "server"},
    "core": {"persistence", "adapters", "server"},
    "persistence": {"core", "adapters", "server"},
    "adapters": {"core", "persistence", "server"},
    "server": {"persistence", "adapters"},
}


def importacoes(arquivo: pathlib.Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(a.name.split(".")[0] for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.add(no.module.split(".")[0])
    return nomes & PACOTES


@pytest.mark.parametrize("camada", sorted(PROIBIDOS))
def test_camada_respeita_regras_de_dependencia(camada):
    for arquivo in (RAIZ / camada).glob("*.py"):
        violacoes = importacoes(arquivo) & PROIBIDOS[camada]
        assert not violacoes, f"{arquivo.name} importa {violacoes}"
