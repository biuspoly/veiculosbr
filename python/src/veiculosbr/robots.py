"""O site deixa este robô abrir a página? Lê o robots.txt (RFC 9309).

Escrito aqui, e não com o urllib.robotparser, porque o de lá não entende * e $
no caminho, e a regra tem de dar a mesma resposta no pacote em R.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from .rede import baixar

NOME_DO_ROBO = "veiculosbr"
VALIDADE_DO_ROBOTS_DIAS = 1


def pode_visitar(texto_do_robots: str, caminho: str, nome_do_robo: str = NOME_DO_ROBO) -> bool:
    regras_para_o_robo, regras_para_todos = _regras_por_grupo(texto_do_robots, nome_do_robo)
    # Um grupo com o nome do robô vale no lugar do grupo "*", não junto dele.
    regras = regras_para_o_robo if regras_para_o_robo is not None else regras_para_todos
    if not regras:
        return True

    melhor_tamanho = -1
    permitido = True
    for tipo, padrao in regras:
        if not _caminho_casa(padrao, caminho):
            continue
        # Vale a regra mais longa; empatou, o Allow ganha.
        if len(padrao) > melhor_tamanho or (len(padrao) == melhor_tamanho and tipo == "allow"):
            melhor_tamanho = len(padrao)
            permitido = tipo == "allow"
    return permitido


def site_permite(endereco: str) -> bool:
    partes = urlsplit(endereco)
    resposta = baixar(f"{partes.scheme}://{partes.netloc}/robots.txt",
                      validade_cache_dias=VALIDADE_DO_ROBOTS_DIAS)
    if resposta.status != 200:
        return True  # sem robots.txt, o site não pôs regra
    caminho = partes.path or "/"
    if partes.query:
        caminho += "?" + partes.query
    return pode_visitar(resposta.texto, caminho)


def _regras_por_grupo(texto_do_robots: str, nome_do_robo: str):
    regras_para_o_robo = None
    regras_para_todos = []
    robos_do_grupo: list[str] = []
    lendo_robos = False

    for linha in texto_do_robots.splitlines():
        linha = linha.split("#", 1)[0].strip()
        if ":" not in linha:
            continue
        campo, valor = (parte.strip() for parte in linha.split(":", 1))
        campo = campo.lower()

        if campo == "user-agent":
            if not lendo_robos:
                robos_do_grupo = []
            robos_do_grupo.append(valor.lower())
            lendo_robos = True
            continue

        lendo_robos = False
        if campo not in ("allow", "disallow") or valor == "":
            continue
        regra = (campo, valor)
        if nome_do_robo.lower() in robos_do_grupo:
            regras_para_o_robo = (regras_para_o_robo or []) + [regra]
        if "*" in robos_do_grupo:
            regras_para_todos.append(regra)

    return regras_para_o_robo, regras_para_todos


def _caminho_casa(padrao: str, caminho: str) -> bool:
    ancorado_no_fim = padrao.endswith("$")
    if ancorado_no_fim:
        padrao = padrao[:-1]
    expressao = "^" + ".*".join(re.escape(pedaco) for pedaco in padrao.split("*"))
    if ancorado_no_fim:
        expressao += "$"
    return re.match(expressao, caminho) is not None
