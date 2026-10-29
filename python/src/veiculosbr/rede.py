"""Toda consulta à internet passa por aqui.

O robô se identifica, espera entre duas consultas ao mesmo site e para de
consultar um site que recusou. Nada é gravado em disco: a mesma consulta feita
de novo na mesma sessão sai da memória, e some quando o Python fecha. Nos
testes, as respostas vêm de arquivos (variável VEICULOSBR_RESPOSTAS_GRAVADAS).
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import httpx

VERSAO = "0.1.1"
ROBO = f"veiculosbr/{VERSAO} (+https://github.com/biuspoly/veiculosbr)"
SEGUNDOS_ENTRE_CONSULTAS_AO_MESMO_SITE = {
    "www.tabelafipebrasil.com": 3.0,
    # O Parallelum aceita 50 consultas por minuto (cabeçalho x-throttle-limit); 1,5 s deixa em 40.
    "fipe.parallelum.com.br": 1.5,
}
SEGUNDOS_DE_ESPERA_DA_RESPOSTA = 30
TENTATIVAS = 2
SEGUNDOS_ANTES_DE_TENTAR_DE_NOVO = 2
# Site que disse "chega" (HTTP 429 ou 403) fica sem consulta por este tempo.
SEGUNDOS_DE_PAUSA_DEPOIS_DE_RECUSA = 600
APELIDO_DO_SITE = {"fipe.parallelum.com.br": "parallelum", "www.tabelafipebrasil.com": "tabelafipebrasil"}


class ErroDeConsulta(Exception):
    """O site respondeu com erro (ou não respondeu)."""


class CotaEsgotada(ErroDeConsulta):
    """O site avisou que a cota de consultas acabou (HTTP 429)."""


class RespostaNaoGravada(ErroDeConsulta):
    """Teste pediu um endereço que não está em casos/respostas."""


@dataclass
class Resposta:
    status: int
    texto: str
    cabecalhos: dict = field(default_factory=dict)


_respostas_desta_sessao: dict[str, Resposta] = {}
_ultima_consulta_por_site: dict[str, float] = {}
_site_pausado_ate: dict[str, float] = {}


def nome_do_arquivo_gravado(endereco: str) -> str:
    """O mesmo nome em R e em Python: o site (com apelido curto, para o caminho
    caber no limite de 100 caracteres do pacote em R) e o resto do endereço, com
    tudo que não é letra, número, ponto ou hífen trocado por _."""
    sem_protocolo = re.sub(r"^https?://", "", endereco)
    site, _, caminho = sem_protocolo.partition("/")
    site = APELIDO_DO_SITE.get(site, site)
    caminho = re.sub(r"^api/v2/", "", caminho)
    return re.sub(r"[^A-Za-z0-9.-]", "_", f"{site}/{caminho}")


def baixar(endereco: str, cabecalhos: dict | None = None) -> Resposta:
    pasta_gravadas = os.environ.get("VEICULOSBR_RESPOSTAS_GRAVADAS", "")
    if pasta_gravadas:
        arquivo = Path(pasta_gravadas) / nome_do_arquivo_gravado(endereco)
        if not arquivo.exists():
            raise RespostaNaoGravada(f"Resposta não gravada para {endereco} ({arquivo.name})")
        return Resposta(200, arquivo.read_text(encoding="utf-8"))

    if endereco in _respostas_desta_sessao:
        return _respostas_desta_sessao[endereco]

    site = urlsplit(endereco).netloc
    pausado_ate = _site_pausado_ate.get(site, 0)
    if time.monotonic() < pausado_ate:
        minutos = round((pausado_ate - time.monotonic()) / 60) or 1
        raise ErroDeConsulta(f"{site} recusou consultas há pouco; nova tentativa em {minutos} min")

    _esperar_a_vez_do_site(site)
    resposta = _consultar_com_nova_tentativa(endereco, {"User-Agent": ROBO, **(cabecalhos or {})})

    if resposta.status_code in (403, 429):
        _site_pausado_ate[site] = time.monotonic() + SEGUNDOS_DE_PAUSA_DEPOIS_DE_RECUSA
    if resposta.status_code == 429:
        raise CotaEsgotada(f"{site} pediu para parar (HTTP 429: limite de consultas)")
    if resposta.status_code == 403:
        raise ErroDeConsulta(f"{site} recusou a consulta (HTTP 403); costuma ser limite de consultas")
    if resposta.status_code == 404:
        return Resposta(404, resposta.text, dict(resposta.headers))
    if resposta.status_code != 200:
        raise ErroDeConsulta(f"{endereco} respondeu HTTP {resposta.status_code}")

    _gravar_se_pedido(endereco, resposta.text)
    _respostas_desta_sessao[endereco] = Resposta(200, resposta.text, dict(resposta.headers))
    return _respostas_desta_sessao[endereco]


def _consultar_com_nova_tentativa(endereco: str, cabecalhos: dict) -> httpx.Response:
    """Erro do lado do servidor (5xx) ou sem resposta: tenta mais uma vez, 2 s depois."""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = httpx.get(endereco, headers=cabecalhos, timeout=SEGUNDOS_DE_ESPERA_DA_RESPOSTA,
                                 follow_redirects=True)
        except httpx.HTTPError as erro:
            if tentativa == TENTATIVAS:
                raise ErroDeConsulta(f"Sem resposta de {endereco}: {erro}") from erro
        else:
            if resposta.status_code < 500 or tentativa == TENTATIVAS:
                return resposta
        time.sleep(SEGUNDOS_ANTES_DE_TENTAR_DE_NOVO)
    raise AssertionError("inalcançável")


def _gravar_se_pedido(endereco: str, texto: str) -> None:
    # Só para quem desenvolve o pacote: VEICULOSBR_GRAVAR_RESPOSTAS guarda a resposta para os testes.
    pasta_para_gravar = os.environ.get("VEICULOSBR_GRAVAR_RESPOSTAS", "")
    if pasta_para_gravar:
        Path(pasta_para_gravar).mkdir(parents=True, exist_ok=True)
        (Path(pasta_para_gravar) / nome_do_arquivo_gravado(endereco)).write_text(texto, encoding="utf-8")


def _esperar_a_vez_do_site(site: str) -> None:
    intervalo = SEGUNDOS_ENTRE_CONSULTAS_AO_MESMO_SITE.get(site, 0)
    ultima = _ultima_consulta_por_site.get(site)
    if ultima is not None:
        falta = intervalo - (time.monotonic() - ultima)
        if falta > 0:
            time.sleep(falta)
    _ultima_consulta_por_site[site] = time.monotonic()
