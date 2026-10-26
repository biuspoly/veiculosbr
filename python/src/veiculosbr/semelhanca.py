"""Quanto o nome do modelo na placa parece com o nome na tabela FIPE (0 a 1).

O cadastro da placa e a FIPE escrevem o mesmo veículo de jeitos diferentes
("15.190 CRM 4X2" e "15-190 E Constellation 2p"), então a comparação é por
palavra: quantas palavras da placa aparecem no nome da FIPE (cobertura, peso
0,8) e quanto as duas listas se sobrepõem (peso 0,2). Número só vale igual;
palavra de 3+ letras aceita erro pequeno de digitação ou abreviação.
O pacote em R faz a mesma conta, conferida pelos mesmos casos de teste.
"""

from __future__ import annotations

import re
import unicodedata

PESO_DA_COBERTURA = 0.8
PESO_DA_SOBREPOSICAO = 0.2
PARECENCA_MINIMA_ENTRE_PALAVRAS = 0.75
NOTA_DE_ABREVIACAO = 0.9


def palavras_do_nome(nome) -> list[str]:
    sem_acento = unicodedata.normalize("NFKD", str(nome or ""))
    sem_acento = "".join(letra for letra in sem_acento if not unicodedata.combining(letra))
    return re.sub(r"[^A-Z0-9]+", " ", sem_acento.upper()).split()


def distancia_de_edicao(primeira: str, segunda: str) -> int:
    """Quantas letras trocar, tirar ou pôr para uma palavra virar a outra (Levenshtein)."""
    linha_anterior = list(range(len(segunda) + 1))
    for posicao_primeira, letra_primeira in enumerate(primeira, start=1):
        linha_atual = [posicao_primeira]
        for posicao_segunda, letra_segunda in enumerate(segunda, start=1):
            custo_da_troca = 0 if letra_primeira == letra_segunda else 1
            linha_atual.append(min(linha_anterior[posicao_segunda] + 1,
                                   linha_atual[posicao_segunda - 1] + 1,
                                   linha_anterior[posicao_segunda - 1] + custo_da_troca))
        linha_anterior = linha_atual
    return linha_anterior[-1]


def parecenca_entre_palavras(palavra_placa: str, palavra_fipe: str) -> float:
    if palavra_placa == palavra_fipe:
        return 1.0
    alguma_tem_numero = any(letra.isdigit() for letra in palavra_placa + palavra_fipe)
    if alguma_tem_numero or len(palavra_placa) < 3 or len(palavra_fipe) < 3:
        return 0.0
    if palavra_fipe.startswith(palavra_placa) or palavra_placa.startswith(palavra_fipe):
        return NOTA_DE_ABREVIACAO
    distancia = distancia_de_edicao(palavra_placa, palavra_fipe)
    parecenca = 1 - distancia / max(len(palavra_placa), len(palavra_fipe))
    return parecenca if parecenca >= PARECENCA_MINIMA_ENTRE_PALAVRAS else 0.0


def semelhanca(nome_na_placa, nome_na_fipe) -> float:
    palavras_placa = palavras_do_nome(nome_na_placa)
    palavras_fipe = palavras_do_nome(nome_na_fipe)
    if not palavras_placa or not palavras_fipe:
        return 0.0

    notas = [max(parecenca_entre_palavras(palavra, outra) for outra in palavras_fipe)
             for palavra in palavras_placa]
    cobertura = sum(notas) / len(notas)

    em_comum = set(palavras_placa) & set(palavras_fipe)
    todas = set(palavras_placa) | set(palavras_fipe)
    sobreposicao = len(em_comum) / len(todas)

    return round(PESO_DA_COBERTURA * cobertura + PESO_DA_SOBREPOSICAO * sobreposicao, 3)
