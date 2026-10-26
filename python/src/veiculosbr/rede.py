"""Toda consulta à internet passa por aqui.

O robô se identifica, espera entre duas consultas ao mesmo site, guarda as
respostas num cache local e, nos testes, lê respostas gravadas em vez de ir à
rede (variável VEICULOSBR_RESPOSTAS_GRAVADAS).
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from platformdirs import user_cache_dir

VERSAO = "0.1.0"
ROBO = f"veiculosbr/{VERSAO} (+https://github.com/biuspoly/veiculosbr)"
SEGUNDOS_ENTRE_CONSULTAS_AO_MESMO_SITE = 3.0
SEGUNDOS_DE_ESPERA_DA_RESPOSTA = 30
TENTATIVAS = 2
SEGUNDOS_ANTES_DE_TENTAR_DE_NOVO = 2
# Site que disse "chega" (HTTP 429 ou 403) fica sem consulta por este tempo.
SEGUNDOS_DE_PAUSA_DEPOIS_DE_RECUSA = 600

APELIDO_DO_SITE = {"fipe.parallelum.com.br": "parallelum", "www.tabelafipebrasil.com": "tabelafipebrasil"}

_ultima_consulta_por_site: dict[str, float] = {}
_site_pausado_ate: dict[str, float] = {}


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


def nome_do_arquivo_gravado(endereco: str) -> str:
    """O mesmo nome em R e em Python: o site (com apelido curto, para o caminho
    caber no limite de 100 caracteres do pacote em R) e o resto do endereço, com
    tudo que não é letra, número, ponto ou hífen trocado por _."""
    sem_protocolo = re.sub(r"^https?://", "", endereco)
    site, _, caminho = sem_protocolo.partition("/")
    site = APELIDO_DO_SITE.get(site, site)
    caminho = re.sub(r"^api/v2/", "", caminho)
    return re.sub(r"[^A-Za-z0-9.-]", "_", f"{site}/{caminho}")


def pasta_do_cache() -> Path | None:
    configurada = os.environ.get("VEICULOSBR_CACHE", "")
    if configurada == "0":
        return None
    return Path(configurada) if configurada else Path(user_cache_dir("veiculosbr"))


def limpar_cache() -> int:
    """Apaga o cache local. Devolve quantos arquivos saíram."""
    pasta = pasta_do_cache()
    if pasta is None or not pasta.exists():
        return 0
    apagados = 0
    for arquivo in pasta.iterdir():
        if arquivo.is_file():
            arquivo.unlink()
            apagados += 1
    return apagados


def baixar(endereco: str, cabecalhos: dict | None = None, validade_cache_dias: float = 0,
           respeitar_ritmo: bool = False) -> Resposta:
    nome_gravado = nome_do_arquivo_gravado(endereco)

    pasta_gravadas = os.environ.get("VEICULOSBR_RESPOSTAS_GRAVADAS", "")
    if pasta_gravadas:
        arquivo = Path(pasta_gravadas) / nome_gravado
        if not arquivo.exists():
            raise RespostaNaoGravada(f"Resposta não gravada para {endereco} ({arquivo.name})")
        return Resposta(200, arquivo.read_text(encoding="utf-8"))

    arquivo_do_cache = _arquivo_do_cache_valido(nome_gravado, validade_cache_dias)
    if arquivo_do_cache is not None:
        return Resposta(200, arquivo_do_cache.read_text(encoding="utf-8"))

    site = urlsplit(endereco).netloc
    pausado_ate = _site_pausado_ate.get(site, 0)
    if time.monotonic() < pausado_ate:
        minutos = round((pausado_ate - time.monotonic()) / 60) or 1
        raise ErroDeConsulta(f"{site} recusou consultas há pouco; nova tentativa em {minutos} min")

    if respeitar_ritmo:
        _esperar_a_vez_do_site(endereco)

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

    _gravar_se_pedido(nome_gravado, resposta.text)
    if validade_cache_dias > 0:
        _guardar_no_cache(nome_gravado, resposta.text)
    return Resposta(200, resposta.text, dict(resposta.headers))


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


def _arquivo_do_cache_valido(nome_gravado: str, validade_cache_dias: float) -> Path | None:
    pasta = pasta_do_cache()
    if pasta is None or validade_cache_dias <= 0:
        return None
    arquivo = pasta / nome_gravado
    if not arquivo.exists():
        return None
    idade_em_dias = (time.time() - arquivo.stat().st_mtime) / 86400
    return arquivo if idade_em_dias <= validade_cache_dias else None


def _guardar_no_cache(nome_gravado: str, texto: str) -> None:
    pasta = pasta_do_cache()
    if pasta is None:
        return
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / nome_gravado).write_text(texto, encoding="utf-8")


def _gravar_se_pedido(nome_gravado: str, texto: str) -> None:
    # VEICULOSBR_GRAVAR_RESPOSTAS: consulta de verdade, guardada para os testes (ferramentas/).
    pasta_para_gravar = os.environ.get("VEICULOSBR_GRAVAR_RESPOSTAS", "")
    if pasta_para_gravar:
        Path(pasta_para_gravar).mkdir(parents=True, exist_ok=True)
        (Path(pasta_para_gravar) / nome_gravado).write_text(texto, encoding="utf-8")


def _esperar_a_vez_do_site(endereco: str) -> None:
    site = urlsplit(endereco).netloc
    ultima = _ultima_consulta_por_site.get(site)
    if ultima is not None:
        falta = SEGUNDOS_ENTRE_CONSULTAS_AO_MESMO_SITE - (time.monotonic() - ultima)
        if falta > 0:
            time.sleep(falta)
    _ultima_consulta_por_site[site] = time.monotonic()
