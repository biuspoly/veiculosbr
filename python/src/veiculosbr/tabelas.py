"""As tabelas de referência que vêm junto com o pacote (pasta dados/).

Origem de cada uma em dados/LEIAME.md: Wikipédia em inglês, coletada em 26/10/2026.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from importlib import resources


def _ler_csv(nome_do_arquivo: str) -> list[dict]:
    arquivo = resources.files("veiculosbr").joinpath("dados", nome_do_arquivo)
    with arquivo.open(encoding="utf-8", newline="") as aberto:
        return list(csv.DictReader(aberto))


@lru_cache(maxsize=1)
def faixas_uf() -> list[dict]:
    faixas = _ler_csv("faixas_uf.csv")
    for faixa in faixas:
        faixa["numero_min"] = int(faixa["numero_min"])
        faixa["numero_max"] = int(faixa["numero_max"])
    return faixas


@lru_cache(maxsize=1)
def pais_por_prefixo() -> dict[str, str]:
    return {linha["prefixo"]: linha["pais"] for linha in _ler_csv("pais_chassi.csv")}


@lru_cache(maxsize=1)
def fabricante_por_codigo() -> dict[str, str]:
    return {linha["codigo"]: linha["fabricante"] for linha in _ler_csv("fabricante_chassi.csv")}
