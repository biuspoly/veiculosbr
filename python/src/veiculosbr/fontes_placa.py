"""De onde vêm os dados do veículo pela placa. Cada fonte é uma função à parte.

- tabelafipebrasil (padrão): a página pública https://www.tabelafipebrasil.com/placa/<placa>.
  O pacote espera 3 s entre consultas e, se o site recusar (limite de
  consultas), fica 10 minutos sem consultá-lo.
- parallelum (só quando pedida): a busca por placa da API do Parallelum, em
  teste ("Alpha"). A cota é de 5 consultas por mês sem token e 10 com o token
  gratuito (VEICULOSBR_FIPE_TOKEN); o pacote avisa quantas sobraram.

Nenhuma das duas é oficial (nem Senatran, nem Detran, nem FIPE). Placa com o
cadastro errado ou desatualizado na origem vem errada aqui também.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field

from selectolax.lexbor import LexborHTMLParser

from .fipe import valor_em_reais
from .placa import placa_limpar, placa_valida
from .rede import ErroDeConsulta, baixar
from .semelhanca import palavras_do_nome

ENDERECO_TABELAFIPEBRASIL = "https://www.tabelafipebrasil.com/placa/{placa}"
ENDERECO_PARALLELUM_PLACA = "https://fipe.parallelum.com.br/api/v2/plates/{placa}"
FONTE_TABELAFIPEBRASIL = "tabelafipebrasil.com (página pública de placa)"
FONTE_PARALLELUM_PLACA = "Parallelum, busca por placa (fipe.parallelum.com.br)"
TEXTO_PLACA_NAO_ENCONTRADA = "placa não encontrada"
TIPO_PELO_SEGMENTO = {"AUTO": "carros", "MOTO": "motos", "CAMINHAO": "caminhoes"}


@dataclass
class Veiculo:
    placa: str
    fonte: str
    marca: str | None = None
    modelo: str | None = None
    ano_fabricacao: int | None = None
    ano_modelo: int | None = None
    cor: str | None = None
    combustivel: str | None = None
    municipio: str | None = None
    uf: str | None = None
    segmento: str | None = None
    final_do_chassi: str | None = None

    def para_dict(self) -> dict:
        return asdict(self)


@dataclass
class FipeDaFonte:
    codigo_fipe: str
    modelo: str
    preco: float | None


@dataclass
class ConsultaDePlaca:
    veiculo: Veiculo | None
    fipe: list[FipeDaFonte] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    falhas: list[str] = field(default_factory=list)


def tipo_pelo_segmento(segmento) -> str | None:
    """carros, motos ou caminhoes; None quando a fonte não diz ou é algo que a FIPE não cobre."""
    palavras = palavras_do_nome(segmento)
    return TIPO_PELO_SEGMENTO.get(palavras[0]) if palavras else None


def consultar_tabelafipebrasil(placa) -> ConsultaDePlaca | None:
    placa = placa_limpar(placa)
    resposta = baixar(ENDERECO_TABELAFIPEBRASIL.format(placa=placa))
    if resposta.status == 404:
        return None
    return ler_pagina_tabelafipebrasil(placa, resposta.texto)


def ler_pagina_tabelafipebrasil(placa: str, html: str) -> ConsultaDePlaca | None:
    pagina = LexborHTMLParser(html)

    campos = {}
    for linha in pagina.css("table.fipeTablePriceDetail tr"):
        celulas = linha.css("td")
        if len(celulas) == 2:
            rotulo = " ".join(palavras_do_nome(celulas[0].text()))
            campos[rotulo] = celulas[1].text(strip=True)
    if not campos:
        return None  # a página não achou a placa

    veiculo = Veiculo(
        placa=placa,
        fonte=FONTE_TABELAFIPEBRASIL,
        marca=campos.get("MARCA"),
        modelo=campos.get("MODELO"),
        ano_fabricacao=_numero_inteiro(campos.get("ANO")),
        ano_modelo=_numero_inteiro(campos.get("ANO MODELO")),
        cor=campos.get("COR"),
        combustivel=campos.get("COMBUSTIVEL"),
        municipio=campos.get("MUNICIPIO"),
        uf=campos.get("UF"),
        segmento=campos.get("SEGMENTO"),
        final_do_chassi=_final_do_chassi(campos.get("CHASSI")),
    )

    fipe = []
    for linha in pagina.css("table.fipe-desktop tr"):
        celulas = linha.css("td")
        if len(celulas) != 3 or "fipeList" in (celulas[0].attributes.get("class") or ""):
            continue  # a linha do cabeçalho
        fipe.append(FipeDaFonte(
            codigo_fipe=celulas[0].text(strip=True),
            modelo=celulas[1].text(strip=True),
            preco=valor_em_reais(celulas[2].text(strip=True)),
        ))
    return ConsultaDePlaca(veiculo, fipe)


def consultar_parallelum(placa) -> ConsultaDePlaca | None:
    placa = placa_limpar(placa)
    token = os.environ.get("VEICULOSBR_FIPE_TOKEN", "")
    cabecalhos = {"X-Subscription-Token": token} if token else None
    resposta = baixar(ENDERECO_PARALLELUM_PLACA.format(placa=placa), cabecalhos)
    consulta = None if resposta.status == 404 else ler_resposta_parallelum(placa, resposta.texto)

    restantes = {nome.lower(): valor for nome, valor in resposta.cabecalhos.items()}.get(
        "x-plate-quota-remaining")
    if restantes is not None:
        if consulta is None:
            consulta = ConsultaDePlaca(veiculo=None)
        consulta.avisos.append(f"Parallelum: restam {restantes} consultas de placa neste mês.")
    return consulta


def ler_resposta_parallelum(placa: str, texto_json: str) -> ConsultaDePlaca | None:
    dados = json.loads(texto_json)
    if not dados.get("brand") and not dados.get("model"):
        return None
    veiculo = Veiculo(
        placa=placa,
        fonte=FONTE_PARALLELUM_PLACA,
        marca=dados.get("brand") or None,
        modelo=dados.get("model") or None,
        # A API devolve um ano só: o de fabricação, conferido contra o tabelafipebrasil.
        ano_fabricacao=_numero_inteiro(dados.get("year")),
        cor=dados.get("color") or None,
        combustivel=dados.get("fuel") or None,
        municipio=dados.get("city") or None,
        uf=dados.get("state") or None,
        segmento=dados.get("segment") or None,
        final_do_chassi=_final_do_chassi(dados.get("chassis")),
    )
    fipe = [FipeDaFonte(item["codeFipe"], item["model"], valor_em_reais(item["price"]))
            for item in dados.get("fipePrices") or []]
    return ConsultaDePlaca(veiculo, fipe)


FONTES_DE_PLACA = {
    "tabelafipebrasil": consultar_tabelafipebrasil,
    "parallelum": consultar_parallelum,
}
# A Parallelum só entra quando pedida: a cota de placa dela é de poucas consultas por mês.
FONTES_PADRAO = ("tabelafipebrasil",)


def placa_consultar(placa, fontes=FONTES_PADRAO) -> ConsultaDePlaca:
    """Tenta as fontes na ordem e para na primeira que achar a placa. Sem
    nenhuma, veiculo fica None; falhas diz o que deu errado em cada fonte."""
    if not placa_valida(placa):
        raise ValueError(f"Placa inválida: {placa!r}")
    if isinstance(fontes, str):
        fontes = (fontes,)
    avisos, falhas = [], []
    for nome_da_fonte in fontes:
        if nome_da_fonte not in FONTES_DE_PLACA:
            raise ValueError(f"Fonte desconhecida: {nome_da_fonte!r} (use {', '.join(FONTES_DE_PLACA)})")
        try:
            consulta = FONTES_DE_PLACA[nome_da_fonte](placa)
        except ErroDeConsulta as erro:
            falhas.append(f"{nome_da_fonte}: {erro}")
            continue
        if consulta is not None:
            avisos.extend(consulta.avisos)
        if consulta is not None and consulta.veiculo is not None:
            consulta.avisos, consulta.falhas = avisos, falhas
            return consulta
        falhas.append(f"{nome_da_fonte}: {TEXTO_PLACA_NAO_ENCONTRADA}")
    return ConsultaDePlaca(veiculo=None, avisos=avisos, falhas=falhas)


def _numero_inteiro(texto) -> int | None:
    numeros = re.sub(r"[^0-9]", "", str(texto or ""))
    return int(numeros) if numeros else None


def _final_do_chassi(texto) -> str | None:
    final = re.sub(r"[^A-Z0-9]", "", str(texto or "").upper())
    return final or None
