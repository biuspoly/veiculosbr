"""Tabela FIPE pelo catálogo: marca, modelo, ano e preço.

Fonte: a API pública do Parallelum (https://fipe.parallelum.com.br/api/v2),
que repete os dados da Fundação Instituto de Pesquisas Econômicas (FIPE).
Sem token: 500 consultas por dia. Com o token gratuito de https://fipe.api.br
na variável VEICULOSBR_FIPE_TOKEN, 1.000 (https://fipe.api.br/docs/api). Entre
duas consultas, o pacote espera 1,5 s: o catálogo aceita até 50 por minuto.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass

from .rede import baixar
from .semelhanca import palavras_do_nome

ENDERECO_DA_API = "https://fipe.parallelum.com.br/api/v2"
FONTE_DO_CATALOGO = "Tabela FIPE, pela API do Parallelum (fipe.parallelum.com.br)"
TIPO_NA_API = {"carros": "cars", "motos": "motorcycles", "caminhoes": "trucks"}
# Na FIPE, carro flex aparece como Gasolina (código 1).
CODIGO_DO_COMBUSTIVEL = {"gasolina": "1", "flex": "1", "alcool": "2", "etanol": "2", "diesel": "3"}
ANO_DO_ZERO_KM = 32000  # convenção da FIPE para o preço do veículo novo


@dataclass
class ItemDoCatalogo:
    codigo: str
    nome: str


@dataclass
class PrecoFipe:
    codigo_fipe: str
    marca: str
    modelo: str
    ano_modelo: int
    combustivel: str
    preco: float
    referencia: str
    fonte: str = FONTE_DO_CATALOGO

    def para_dict(self) -> dict:
        return asdict(self)


def valor_em_reais(texto) -> float | None:
    """'R$ 257.276,00' -> 257276.0"""
    numeros = re.sub(r"[^0-9,]", "", str(texto or ""))
    if not numeros:
        return None
    return float(numeros.replace(",", "."))


def codigo_do_combustivel(combustivel) -> str | None:
    for palavra in palavras_do_nome(combustivel):
        codigo = CODIGO_DO_COMBUSTIVEL.get(palavra.lower())
        if codigo:
            return codigo
    return None


def fipe_referencias() -> list[ItemDoCatalogo]:
    """Os meses da tabela FIPE (o código de cada mês e o nome dele)."""
    return [ItemDoCatalogo(item["code"], item["month"]) for item in _consultar("/references")]


def fipe_marcas(tipo: str) -> list[ItemDoCatalogo]:
    return _itens(_consultar(f"/{_tipo_na_api(tipo)}/brands"))


def fipe_modelos(tipo: str, marca: str) -> list[ItemDoCatalogo]:
    """marca é o código da marca (veja fipe_marcas)."""
    return _itens(_consultar(f"/{_tipo_na_api(tipo)}/brands/{marca}/models"))


def fipe_anos_da_marca(tipo: str, marca: str) -> list[ItemDoCatalogo]:
    """Os anos (com o combustível, ex. 2018-3) que a marca tem na tabela."""
    return _itens(_consultar(f"/{_tipo_na_api(tipo)}/brands/{marca}/years"))


def fipe_modelos_do_ano(tipo: str, marca: str, ano: str) -> list[ItemDoCatalogo]:
    """Só os modelos da marca que existem naquele ano (ano no formato 2018-3)."""
    return _itens(_consultar(f"/{_tipo_na_api(tipo)}/brands/{marca}/years/{ano}/models"))


def fipe_anos(tipo: str, codigo_fipe: str) -> list[ItemDoCatalogo]:
    return _itens(_consultar(f"/{_tipo_na_api(tipo)}/{codigo_fipe}/years"))


def fipe_preco(tipo: str, codigo_fipe: str, ano) -> list[PrecoFipe]:
    """ano: 2018 traz todos os combustíveis daquele ano; '2018-3' traz só aquele."""
    codigos_de_ano = _codigos_do_ano(fipe_anos(tipo, codigo_fipe), ano)
    precos = []
    for codigo_do_ano in codigos_de_ano:
        detalhe = _consultar(f"/{_tipo_na_api(tipo)}/{codigo_fipe}/years/{codigo_do_ano}")
        if detalhe:
            precos.append(_preco_do_detalhe(detalhe))
    return precos


def fipe_precos_da_marca(tipo: str, marca: str, ano) -> list[PrecoFipe]:
    """Os preços de todos os modelos da marca num ano, já com o código FIPE de cada um.

    Uma consulta por modelo (mais uma ou duas): uma marca grande leva mais de um minuto e
    pesa na cota diária. ano: 2018
    traz todos os combustíveis daquele ano; '2018-3' traz só aquele.
    """
    precos = []
    for codigo_do_ano in _codigos_do_ano(fipe_anos_da_marca(tipo, marca), ano):
        for modelo in fipe_modelos_do_ano(tipo, marca, codigo_do_ano):
            preco = fipe_preco_do_modelo(tipo, marca, modelo.codigo, codigo_do_ano)
            if preco is not None:
                precos.append(preco)
    return precos


def fipe_preco_do_modelo(tipo: str, marca: str, modelo: str, ano: str) -> PrecoFipe | None:
    """O preço pelo código do modelo (não o código FIPE), como a busca de candidatos acha."""
    detalhe = _consultar(f"/{_tipo_na_api(tipo)}/brands/{marca}/models/{modelo}/years/{ano}")
    return _preco_do_detalhe(detalhe) if detalhe else None


def _codigos_do_ano(anos: list[ItemDoCatalogo], ano) -> list[str]:
    if isinstance(ano, str) and "-" in ano:
        return [item.codigo for item in anos if item.codigo == ano]
    return [item.codigo for item in anos if item.codigo.split("-")[0] == str(ano)]


def _preco_do_detalhe(detalhe: dict) -> PrecoFipe:
    return PrecoFipe(
        codigo_fipe=detalhe["codeFipe"],
        marca=detalhe["brand"],
        modelo=detalhe["model"],
        ano_modelo=int(detalhe["modelYear"]),
        combustivel=detalhe["fuel"],
        preco=valor_em_reais(detalhe["price"]),
        referencia=detalhe["referenceMonth"],
    )


def _itens(lista: list[dict]) -> list[ItemDoCatalogo]:
    return [ItemDoCatalogo(str(item["code"]), item["name"]) for item in lista]


def _tipo_na_api(tipo: str) -> str:
    if tipo not in TIPO_NA_API:
        raise ValueError(f"tipo deve ser um destes: {', '.join(TIPO_NA_API)} (veio {tipo!r})")
    return TIPO_NA_API[tipo]


def _consultar(caminho: str):
    token = os.environ.get("VEICULOSBR_FIPE_TOKEN", "")
    cabecalhos = {"X-Subscription-Token": token} if token else None
    resposta = baixar(ENDERECO_DA_API + caminho, cabecalhos)
    if resposta.status == 404:
        return []
    return json.loads(resposta.texto)
