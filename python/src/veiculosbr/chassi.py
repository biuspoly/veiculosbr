"""Chassi (VIN): 17 caracteres, sem I, O e Q (norma ISO 3779).

Os 2 primeiros dizem o país, os 3 primeiros o fabricante, o 10º o ano-modelo.
O 9º só é dígito verificador nos veículos da América do Norte e da China: no
Brasil não é obrigatório, então chassi_valido não o confere.
"""

from __future__ import annotations

import re
from datetime import date

from .tabelas import fabricante_por_codigo, pais_por_prefixo

FORMATO_DO_CHASSI = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
# 30 códigos de ano: A = 1980 ... Y = 2000, 1 = 2001 ... 9 = 2009, e o ciclo recomeça em 2010.
CODIGOS_DE_ANO = "ABCDEFGHJKLMNPRSTVWXY123456789"
VALOR_DA_LETRA = dict(zip("ABCDEFGHJKLMNPRSTUVWXYZ", (1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 7, 9, 2,
                                                       3, 4, 5, 6, 7, 8, 9)))
PESOS_DO_DIGITO_9 = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)


def chassi_limpar(chassi) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(chassi or "").upper())


def chassi_valido(chassi) -> bool:
    return FORMATO_DO_CHASSI.match(chassi_limpar(chassi)) is not None


def chassi_pais(chassi) -> str | None:
    chassi = chassi_limpar(chassi)
    if not chassi_valido(chassi):
        return None
    paises = pais_por_prefixo()
    return paises.get(chassi[:2]) or paises.get(chassi[:1])


def chassi_fabricante(chassi) -> str | None:
    """Só os fabricantes com fábrica no Brasil estão na tabela (o nome vem
    como a fonte escreve, em inglês)."""
    chassi = chassi_limpar(chassi)
    if not chassi_valido(chassi):
        return None
    return fabricante_por_codigo().get(chassi[:3])


def chassi_ano_modelo(chassi, ano_referencia: int | None = None) -> int | None:
    """O código do ano se repete a cada 30 anos (A = 1980 ou 2010): fica o mais
    recente que não passe de ano_referencia + 1 (padrão: o ano de hoje)."""
    chassi = chassi_limpar(chassi)
    if not chassi_valido(chassi) or chassi[9] not in CODIGOS_DE_ANO:
        return None
    ano_referencia = ano_referencia or date.today().year
    posicao = CODIGOS_DE_ANO.index(chassi[9])
    anos_possiveis = [1980 + posicao + 30 * ciclo for ciclo in range(4)]
    anos_que_cabem = [ano for ano in anos_possiveis if ano <= ano_referencia + 1]
    return max(anos_que_cabem) if anos_que_cabem else None


def chassi_digito9_confere(chassi) -> bool:
    chassi = chassi_limpar(chassi)
    if not chassi_valido(chassi):
        return False
    soma = 0
    for caractere, peso in zip(chassi, PESOS_DO_DIGITO_9):
        valor = int(caractere) if caractere.isdigit() else VALOR_DA_LETRA[caractere]
        soma += valor * peso
    resto = soma % 11
    digito_esperado = "X" if resto == 10 else str(resto)
    return chassi[8] == digito_esperado
