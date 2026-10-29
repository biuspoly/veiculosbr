"""Copia dados/ e casos/ para dentro dos dois pacotes, e o README e a LICENSE para o do Python.

Cada pacote precisa da sua cópia (o R instala só o que está em r/, o Python só
o que está em python/). A fonte é sempre a raiz: mudou lá, rode este script.
O teste test_copias_iguais acusa cópia esquecida. O LEIAME.md de dados/ vai
junto porque diz a licença da tabela (CC BY-SA, que exige a atribuição).

Uso: python ferramentas/sincronizar.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
COPIAS = {
    RAIZ / "dados": [RAIZ / "python" / "src" / "veiculosbr" / "dados", RAIZ / "r" / "inst" / "extdata"],
    RAIZ / "casos": [RAIZ / "r" / "tests" / "testthat" / "casos"],
}
# O PyPI mostra o README que está dentro de python/, e o pacote leva a LICENSE de lá.
ARQUIVOS_DO_PYTHON = ["README.md", "LICENSE"]


def copiar_pasta(origem: Path, destino: Path) -> int:
    if destino.exists():
        shutil.rmtree(destino)
    copiados = 0
    for arquivo in origem.rglob("*"):
        if arquivo.is_file():
            alvo = destino / arquivo.relative_to(origem)
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(arquivo, alvo)
            copiados += 1
    return copiados


if __name__ == "__main__":
    for origem, destinos in COPIAS.items():
        for destino in destinos:
            quantidade = copiar_pasta(origem, destino)
            print(f"{origem.name}/ -> {destino.relative_to(RAIZ)} ({quantidade} arquivos)")
    for nome in ARQUIVOS_DO_PYTHON:
        shutil.copyfile(RAIZ / nome, RAIZ / "python" / nome)
        print(f"{nome} -> python/{nome}")
