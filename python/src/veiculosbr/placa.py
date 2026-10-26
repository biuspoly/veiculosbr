"""Placa de veículo: a antiga (ABC1234) e a Mercosul (ABC1D23).

Na conversão para a Mercosul, o 2º número vira letra: 0 = A, 1 = B ... 9 = J.
O estado vem das letras: cada estado recebeu faixas próprias (dados/faixas_uf.csv).
"""

from __future__ import annotations

import re

from .tabelas import faixas_uf

FORMATO_ANTIGO = re.compile(r"^[A-Z]{3}[0-9]{4}$")
FORMATO_MERCOSUL = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")
LETRAS_DO_QUINTO_CARACTERE = "ABCDEFGHIJ"


def placa_limpar(placa) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(placa or "").upper())


def placa_tipo(placa) -> str | None:
    placa = placa_limpar(placa)
    if FORMATO_ANTIGO.match(placa):
        return "antiga"
    if FORMATO_MERCOSUL.match(placa):
        return "mercosul"
    return None


def placa_valida(placa) -> bool:
    return placa_tipo(placa) is not None


def placa_para_mercosul(placa) -> str | None:
    placa = placa_limpar(placa)
    tipo = placa_tipo(placa)
    if tipo == "mercosul":
        return placa
    if tipo == "antiga":
        segundo_numero = int(placa[4])
        return placa[:4] + LETRAS_DO_QUINTO_CARACTERE[segundo_numero] + placa[5:]
    return None


def placa_para_antiga(placa) -> str | None:
    """A placa Mercosul que já nasceu Mercosul nunca teve versão antiga; a
    conversão devolve a que ela TERIA. Só as letras de A a J têm número."""
    placa = placa_limpar(placa)
    tipo = placa_tipo(placa)
    if tipo == "antiga":
        return placa
    if tipo == "mercosul" and placa[4] in LETRAS_DO_QUINTO_CARACTERE:
        return placa[:4] + str(LETRAS_DO_QUINTO_CARACTERE.index(placa[4])) + placa[5:]
    return None


def placa_formatar(placa) -> str | None:
    """A antiga com hífen (ABC-1234); a Mercosul sem (ABC1D23), como sai na placa."""
    placa = placa_limpar(placa)
    tipo = placa_tipo(placa)
    if tipo == "antiga":
        return placa[:3] + "-" + placa[3:]
    if tipo == "mercosul":
        return placa
    return None


def placa_uf(placa) -> str | None:
    """O estado que recebeu a faixa de letras da placa: é onde o veículo foi
    emplacado pela primeira vez, não onde está registrado hoje."""
    placa = placa_limpar(placa)
    if not placa_valida(placa):
        return None
    letras = placa[:3]
    placa_antiga = placa_para_antiga(placa)
    # Sem o número (Mercosul com letra depois do J), decidem só as letras, se der um estado só.
    numero = int(placa_antiga[3:]) if placa_antiga else None

    estados = set()
    for faixa in faixas_uf():
        dentro_das_letras = faixa["inicio"] <= letras <= faixa["fim"]
        dentro_dos_numeros = numero is None or faixa["numero_min"] <= numero <= faixa["numero_max"]
        if dentro_das_letras and dentro_dos_numeros:
            estados.add(faixa["uf"])
    return estados.pop() if len(estados) == 1 else None
