"""A tabela de faixas de placa por estado, que vem junto com o pacote (pasta dados/).

Origem em dados/LEIAME.md: Wikipédia em inglês, coletada em 26/10/2026.
"""

from __future__ import annotations

import csv
import io
from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=1)
def faixas_uf() -> list[dict]:
    texto = resources.files("veiculosbr").joinpath("dados", "faixas_uf.csv").read_text(encoding="utf-8")
    faixas = list(csv.DictReader(io.StringIO(texto)))
    for faixa in faixas:
        faixa["numero_min"] = int(faixa["numero_min"])
        faixa["numero_max"] = int(faixa["numero_max"])
    return faixas
