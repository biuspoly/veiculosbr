"""Refaz as tabelas de dados/ a partir da Wikipédia em inglês.

- dados/faixas_uf.csv: as letras da placa e o estado que as recebeu
  ("Vehicle registration plates of Brazil", seção "Vertical Distribution of
  Alphanumeric Combinations", que cita o Sinesp/Senatran).
- dados/pais_chassi.csv e dados/fabricante_chassi.csv: o país pelos 2
  primeiros caracteres do chassi e o fabricante brasileiro pelos 3 primeiros
  ("Vehicle identification number", seções "Country or region codes" e
  "List of many WMIs").

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
PAGINA_CHASSI = "Vehicle_identification_number"

# A ordem dos caracteres nos intervalos de país do chassi (norma ISO 3779):
# letras sem I, O e Q, depois 1 a 9, e o 0 por último.
ORDEM_CHASSI = "ABCDEFGHJKLMNPRSTUVWXYZ1234567890"

PAIS_EM_PORTUGUES = {
    "South Africa": "África do Sul", "Côte d'Ivoire": "Costa do Marfim", "Lesotho": "Lesoto",
    "Botswana": "Botsuana", "Namibia": "Namíbia", "Madagascar": "Madagascar",
    "Mauritius": "Maurício", "Tunisia": "Tunísia", "Cyprus": "Chipre", "Zimbabwe": "Zimbábue",
    "Mozambique": "Moçambique", "Angola": "Angola", "Ethiopia": "Etiópia", "Kenya": "Quênia",
    "Rwanda": "Ruanda", "Nigeria": "Nigéria", "Algeria": "Argélia", "Swaziland": "Essuatíni",
    "Uganda": "Uganda", "Libya": "Líbia", "Egypt": "Egito", "Morocco": "Marrocos",
    "Zambia": "Zâmbia", "China": "China", "Japan": "Japão", "Israel": "Israel",
    "South Korea": "Coreia do Sul", "Jordan": "Jordânia", "Kyrgyzstan": "Quirguistão",
    "India": "Índia", "Indonesia": "Indonésia", "Thailand": "Tailândia", "Myanmar": "Mianmar",
    "Mongolia": "Mongólia", "Kazakhstan": "Cazaquistão", "Iran": "Irã", "Pakistan": "Paquistão",
    "Iraq": "Iraque", "Turkey": "Turquia", "Uzbekistan": "Uzbequistão",
    "Azerbaijan": "Azerbaijão", "Tajikistan": "Tajiquistão", "Armenia": "Armênia",
    "Philippines": "Filipinas", "Singapore": "Singapura", "Malaysia": "Malásia",
    "Bangladesh": "Bangladesh", "Cambodia": "Camboja",
    "United Arab Emirates": "Emirados Árabes Unidos", "Taiwan": "Taiwan", "Vietnam": "Vietnã",
    "Laos": "Laos", "Saudi Arabia": "Arábia Saudita", "Hong Kong": "Hong Kong",
    "Russia": "Rússia", "United Kingdom": "Reino Unido", "Germany": "Alemanha",
    "Poland": "Polônia", "Latvia": "Letônia", "Georgia": "Geórgia", "Iceland": "Islândia",
    "Switzerland": "Suíça", "Czech Republic": "República Tcheca", "Hungary": "Hungria",
    "Portugal": "Portugal", "Serbia": "Sérvia", "Andorra": "Andorra",
    "Netherlands": "Países Baixos", "Spain": "Espanha", "Denmark": "Dinamarca",
    "Ireland": "Irlanda", "Romania": "Romênia", "North Macedonia": "Macedônia do Norte",
    "Slovakia": "Eslováquia", "Bosnia and Herzegovina": "Bósnia e Herzegovina",
    "Austria": "Áustria", "France": "França", "Croatia": "Croácia", "Estonia": "Estônia",
    "Bulgaria": "Bulgária", "Greece": "Grécia", "Luxembourg": "Luxemburgo",
    "Belgium": "Bélgica", "Finland": "Finlândia", "Malta": "Malta", "Sweden": "Suécia",
    "Norway": "Noruega", "Belarus": "Belarus", "Ukraine": "Ucrânia", "Italy": "Itália",
    "Slovenia": "Eslovênia", "San Marino": "San Marino", "Lithuania": "Lituânia",
    "United States": "Estados Unidos", "Canada": "Canadá", "Mexico": "México",
    "Nicaragua": "Nicarágua", "Dominican Republic": "República Dominicana",
    "Honduras": "Honduras", "Panama": "Panamá", "Puerto Rico": "Porto Rico",
    "Australia": "Austrália", "New Zealand": "Nova Zelândia", "Argentina": "Argentina",
    "Chile": "Chile", "Ecuador": "Equador", "Peru": "Peru", "Venezuela": "Venezuela",
    "Bolivia": "Bolívia", "Costa Rica": "Costa Rica", "Brazil": "Brasil",
    "Colombia": "Colômbia", "Uruguay": "Uruguai",
}


def baixar_texto_da_pagina(titulo: str) -> str:
    endereco = f"https://en.wikipedia.org/w/index.php?title={titulo}&action=raw"
    pedido = urllib.request.Request(endereco, headers={"User-Agent": ROBO})
    with urllib.request.urlopen(pedido, timeout=60) as resposta:
        return resposta.read().decode("utf-8")


def tirar_marcacao_wiki(texto: str) -> str:
    texto = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>|<[^>]+>", "", texto)
    texto = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", texto)
    return re.sub(r"\s+", " ", texto).strip()


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


def paises_do_chassi(texto_da_pagina: str) -> list[dict]:
    paises = []
    for linha in texto_da_pagina.splitlines():
        achou = re.match(r"^'''([0-9A-Z]{1,2})(?:[-–]([0-9A-Z]{1,2}))?'''\s*(.+)$", linha)
        if not achou:
            continue
        nome_em_ingles = re.sub(r"\(.*?\)", "", tirar_marcacao_wiki(achou.group(3))).strip()
        if nome_em_ingles not in PAIS_EM_PORTUGUES:
            sys.exit(f"País sem tradução em PAIS_EM_PORTUGUES: {nome_em_ingles!r}")
        pais = PAIS_EM_PORTUGUES[nome_em_ingles]
        primeiro, ultimo = achou.group(1), achou.group(2) or achou.group(1)
        if len(primeiro) == 1:
            paises.append({"prefixo": primeiro, "pais": pais})
            continue
        letra_inicial = primeiro[0]
        posicao_inicio = ORDEM_CHASSI.index(primeiro[1])
        posicao_fim = ORDEM_CHASSI.index(ultimo[1])
        for segundo_caractere in ORDEM_CHASSI[posicao_inicio:posicao_fim + 1]:
            paises.append({"prefixo": letra_inicial + segundo_caractere, "pais": pais})
    # Um prefixo de 2 caracteres vale mais que o de 1 (6Y é Nova Zelândia, o resto do 6 é Austrália).
    por_prefixo = {}
    for linha in paises:
        por_prefixo[linha["prefixo"]] = linha
    return sorted(por_prefixo.values(), key=lambda linha: linha["prefixo"])


def fabricantes_brasileiros(texto_da_pagina: str) -> list[dict]:
    fabricantes = []
    dentro_do_brasil = False
    for linha in texto_da_pagina.splitlines():
        achou = re.match(r"^\| ([0-9A-Z]{3}) \|\|(.*)$", linha)
        if not achou:
            continue
        codigo, resto = achou.group(1), achou.group(2)
        if "Brazil" in resto and "rowspan" in resto:
            dentro_do_brasil = True
            resto = resto.split("Brazil ||", 1)[1]
        elif "rowspan" in resto or "||" in resto:
            # Uma linha com país próprio fecha o bloco do Brasil.
            dentro_do_brasil = False
        if dentro_do_brasil:
            fabricante = tirar_marcacao_wiki(resto).strip("| ").strip()
            fabricantes.append({"codigo": codigo, "fabricante": fabricante})
    if len(fabricantes) < 30:
        sys.exit(f"Só {len(fabricantes)} fabricantes brasileiros: a página mudou de formato?")
    return sorted(fabricantes, key=lambda linha: linha["codigo"])


def gravar_csv(nome_do_arquivo: str, linhas: list[dict]) -> None:
    caminho = PASTA_DADOS / nome_do_arquivo
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"{caminho.name}: {len(linhas)} linhas")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    texto_placas = baixar_texto_da_pagina(PAGINA_PLACAS)
    texto_chassi = baixar_texto_da_pagina(PAGINA_CHASSI)
    gravar_csv("faixas_uf.csv", faixas_por_estado(texto_placas))
    gravar_csv("pais_chassi.csv", paises_do_chassi(texto_chassi))
    gravar_csv("fabricante_chassi.csv", fabricantes_brasileiros(texto_chassi))
    print(f"Coletado em {date.today():%d/%m/%Y}: atualize a data em dados/LEIAME.md.")
