"""Consulta pela linha de comando: python -m veiculosbr PLACA [PLACA ...]

Mostra tudo o que o pacote sabe da placa: formato, estado de origem, o veículo
pela fonte e os candidatos FIPE, com o aviso de que pode haver erro.
"""

from __future__ import annotations

import argparse
import sys

from .fipe_placa import fipe_por_placa
from .placa import placa_para_antiga, placa_para_mercosul, placa_tipo, placa_uf, placa_valida


def mostrar_placa(placa: str) -> None:
    print(f"=== {placa}")
    if not placa_valida(placa):
        print("placa inválida")
        return
    print(f"formato:             {placa_tipo(placa)}")
    print(f"na Mercosul:         {placa_para_mercosul(placa)}")
    print(f"no formato antigo:   {placa_para_antiga(placa) or '-'}")
    print(f"estado de origem:    {placa_uf(placa) or 'faixa desconhecida'}")

    resultado = fipe_por_placa(placa)
    if resultado.veiculo is not None:
        for campo, valor in resultado.veiculo.para_dict().items():
            if campo != "placa":
                print(f"{campo + ':':<21}{valor if valor is not None else '-'}")
    for numero, candidato in enumerate(resultado.candidatos, start=1):
        preco = "sem preço" if candidato.preco is None else (
            f"R$ {candidato.preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print(f"FIPE {numero}: {candidato.codigo_fipe}  {candidato.modelo_fipe}  {candidato.ano_modelo}  "
              f"{preco}  ({candidato.referencia or 'mês não informado'}; confiança {candidato.confianca}; "
              f"semelhança {candidato.semelhanca})")
    for aviso in resultado.avisos:
        print(f"aviso: {aviso}")
    for falha in resultado.falhas:
        print(f"falha: {falha}")
    print()


def principal() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    leitor = argparse.ArgumentParser(prog="veiculosbr", description=__doc__.splitlines()[0])
    leitor.add_argument("placas", nargs="*", help="uma ou mais placas")
    argumentos = leitor.parse_args()
    placas = argumentos.placas or input("Placa: ").split()
    for placa in placas:
        mostrar_placa(placa)


if __name__ == "__main__":
    principal()
