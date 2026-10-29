"""Os casos de casos/*.json: os mesmos que o pacote em R confere."""

import pytest
from conftest import ler_casos

from veiculosbr import (
    fipe_por_placa,
    fipe_precos_da_marca,
    placa_formatar,
    placa_para_antiga,
    placa_para_mercosul,
    placa_tipo,
    placa_uf,
    placa_valida,
    renavam_valido,
)
from veiculosbr.renavam import renavam_limpar
from veiculosbr.semelhanca import semelhanca


@pytest.mark.parametrize("caso", ler_casos("placa.json"), ids=lambda caso: str(caso["placa"]))
def test_placa(caso):
    placa = caso["placa"]
    assert placa_valida(placa) == caso["valida"]
    assert placa_tipo(placa) == caso["tipo"]
    assert placa_para_mercosul(placa) == caso["mercosul"]
    assert placa_para_antiga(placa) == caso["antiga"]
    assert placa_formatar(placa) == caso["formatada"]
    assert placa_uf(placa) == caso["uf"]


@pytest.mark.parametrize("caso", ler_casos("renavam.json"), ids=lambda caso: str(caso["renavam"]))
def test_renavam(caso):
    assert renavam_limpar(caso["renavam"]) == caso["limpo"]
    assert renavam_valido(caso["renavam"]) == caso["valido"]


@pytest.mark.parametrize("caso", ler_casos("semelhanca.json"), ids=lambda caso: f"{caso['placa']}~{caso['fipe']}")
def test_semelhanca(caso):
    assert semelhanca(caso["placa"], caso["fipe"]) == caso["semelhanca"]


@pytest.mark.parametrize("caso", ler_casos("fipe_por_placa.json"), ids=lambda caso: caso["descricao"])
def test_fipe_por_placa(caso):
    resultado = fipe_por_placa(caso["placa"], fontes=caso["fontes"], conferir=caso["conferir"])

    assert (resultado.veiculo is not None) == caso["encontrou"]
    if caso["encontrou"]:
        assert resultado.veiculo.marca == caso["marca"]
        assert resultado.veiculo.ano_modelo == caso["ano_modelo_do_veiculo"]

    obtidos = [{campo: getattr(candidato, campo) for campo in esperado}
               for candidato, esperado in zip(resultado.candidatos, caso["candidatos"])]
    assert len(resultado.candidatos) == len(caso["candidatos"])
    assert obtidos == caso["candidatos"]

    todos_os_avisos = " | ".join(resultado.avisos)
    for trecho in caso["aviso_contem"]:
        assert trecho in todos_os_avisos
    todas_as_falhas = " | ".join(resultado.falhas)
    for trecho in caso.get("falha_contem", []):
        assert trecho in todas_as_falhas


@pytest.mark.parametrize("caso", ler_casos("fipe_precos_da_marca.json"), ids=lambda caso: caso["descricao"])
def test_fipe_precos_da_marca(caso):
    precos = fipe_precos_da_marca(caso["tipo"], caso["marca"], caso["ano"])
    obtidos = [{campo: getattr(preco, campo) for campo in esperado}
               for preco, esperado in zip(precos, caso["precos"])]
    assert len(precos) == len(caso["precos"])
    assert obtidos == caso["precos"]
