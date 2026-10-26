"""RENAVAM: 11 dígitos, o último confere os 10 primeiros (módulo 11).

O RENAVAM antigo tinha 9 dígitos; ele vale com dois zeros na frente.
"""

from __future__ import annotations

import re

PESOS = (3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def renavam_limpar(renavam) -> str:
    numeros = re.sub(r"[^0-9]", "", str(renavam or ""))
    if len(numeros) == 9:
        numeros = numeros.zfill(11)
    return numeros


def renavam_digito(dez_primeiros_digitos: str) -> int:
    soma = sum(int(digito) * peso for digito, peso in zip(dez_primeiros_digitos, PESOS))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto


def renavam_valido(renavam) -> bool:
    numeros = renavam_limpar(renavam)
    if len(numeros) != 11 or numeros == "0" * 11:
        return False
    return renavam_digito(numeros[:10]) == int(numeros[10])
