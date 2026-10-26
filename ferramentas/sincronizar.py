"""Copia dados/ e casos/ para dentro dos dois pacotes.

Cada pacote precisa da sua cópia (o R instala só o que está em r/, o Python só
o que está em python/src/). A fonte é sempre a pasta da raiz: mudou lá, rode
este script. O teste test_copias_iguais.py acusa cópia esquecida.

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
# O PyPI mostra o README que está dentro de python/.
README_DO_PYTHON = (RAIZ / "README.md", RAIZ / "python" / "README.md")


def copiar_pasta(origem: Path, destino: Path) -> int:
    if destino.exists():
        shutil.rmtree(destino)
    copiados = 0
    for arquivo in origem.rglob("*"):
        if arquivo.is_file() and arquivo.name != "LEIAME.md":
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
    shutil.copyfile(*README_DO_PYTHON)
    print("README.md -> python/README.md")
