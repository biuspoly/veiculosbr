"""Refaz dados/faixas_uf.csv a partir da Wikipédia em inglês.

As letras da placa e o estado que as recebeu: página "Vehicle registration
plates of Brazil", seção "Vertical Distribution of Alphanumeric Combinations",
que cita o Sinesp/Senatran.

Uso: python ferramentas/gerar_tabelas.py   (depois, python ferramentas/sincronizar.py)
"""

from __future__ import annotations

import csv
import re
import sys
import urllib.request
from datetime import date
from itertools import pairwise
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"
ROBO = "veiculosbr/0.1 (+https://github.com/biuspoly/veiculosbr)"
PAGINA_PLACAS = "Vehicle_registration_plates_of_Brazil"


def baixar_texto_da_pagina(titulo: str) -> str:
    endereco = f"https://en.wikipedia.org/w/index.php?title={titulo}&action=raw"
    pedido = urllib.request.Request(endereco, headers={"User-Agent": ROBO})
    with urllib.request.urlopen(pedido, timeout=60) as resposta:
        return resposta.read().decode("utf-8")


def faixas_por_estado(texto_da_pagina: str) -> list[dict]:
    inicio = texto_da_pagina.index("===Vertical Distribution")
    tabela = texto_da_pagina[inicio:texto_da_pagina.index("|}", inicio)]
    faixas = []
    for linha_do_estado in re.split(r"\n\|-\n", tabela):
        achou_estado = re.search(r"\{\{flag\|[^}]*\}\}(?:\|name=[^(]*)?\s*\((\w\w)\)", linha_do_estado)
        if not achou_estado:
            continue
        uf = achou_estado.group(1)
        celulas = linha_do_estado[achou_estado.end():].replace("\n", " ").split("||")
        sequencia = 0
        for celula in celulas:
            celula = re.sub(r"\s+", " ", celula.strip("| ").strip()).replace(" a ", " to ")
            if not celula:
                continue
            sequencia += 1
            # A série SAV foi dividida: até o número 1000 é de SP, dali em diante do CE.
            if celula.startswith("SAV 0A01"):
                faixas.append(_faixa("SAV", "SAV", 1, 1000, uf, sequencia))
                continue
            if celula.startswith("SAV 1A01"):
                faixas.append(_faixa("SAV", "SAV", 1001, 9999, uf, sequencia))
                faixas.append(_faixa("SAW", "SBV", 1, 9999, uf, sequencia))
                continue
            letras = re.fullmatch(r"([A-Z]{3})(?: to ([A-Z]{3}))?", celula)
            if not letras:
                sys.exit(f"Célula da tabela de placas que não entendi ({uf}): {celula!r}")
            faixas.append(_faixa(letras.group(1), letras.group(2) or letras.group(1), 1, 9999, uf, sequencia))
    faixas.sort(key=lambda faixa: (faixa["inicio"], faixa["numero_min"]))
    for anterior, seguinte in pairwise(faixas):
        if seguinte["inicio"] <= anterior["fim"] and seguinte["numero_min"] <= anterior["numero_max"]:
            sys.exit(f"Faixas sobrepostas: {anterior} e {seguinte}")
    return faixas


def _faixa(inicio, fim, numero_min, numero_max, uf, sequencia) -> dict:
    return {"inicio": inicio, "fim": fim, "numero_min": numero_min, "numero_max": numero_max,
            "uf": uf, "sequencia": sequencia}


def gravar_csv(nome_do_arquivo: str, linhas: list[dict]) -> None:
    caminho = PASTA_DADOS / nome_do_arquivo
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"{caminho.name}: {len(linhas)} linhas")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    gravar_csv("faixas_uf.csv", faixas_por_estado(baixar_texto_da_pagina(PAGINA_PLACAS)))
    print(f"Coletado em {date.today():%d/%m/%Y}: atualize a data em dados/LEIAME.md e no README.")
