"""Os casos de casos/*.json: os mesmos que o pacote em R confere."""

import pytest
from conftest import ler_casos

from veiculosbr import (
    chassi_ano_modelo,
    chassi_digito9_confere,
    chassi_fabricante,
    chassi_pais,
    chassi_valido,
    fipe_por_placa,
    placa_formatar,
    placa_para_antiga,
    placa_para_mercosul,
    placa_tipo,
    placa_uf,
    placa_valida,
    renavam_limpar,
    renavam_valido,
    semelhanca,
)
from veiculosbr.robots import pode_visitar


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


@pytest.mark.parametrize("caso", ler_casos("chassi.json"),
                         ids=lambda caso: f"{caso['chassi']}-{caso['ano_referencia']}")
def test_chassi(caso):
    chassi = caso["chassi"]
    assert chassi_valido(chassi) == caso["valido"]
    assert chassi_pais(chassi) == caso["pais"]
    assert chassi_fabricante(chassi) == caso["fabricante"]
    assert chassi_digito9_confere(chassi) == caso["digito9_confere"]
    assert chassi_ano_modelo(chassi, caso["ano_referencia"]) == caso["ano_modelo"]


@pytest.mark.parametrize("caso", ler_casos("semelhanca.json"), ids=lambda caso: f"{caso['placa']}~{caso['fipe']}")
def test_semelhanca(caso):
    assert semelhanca(caso["placa"], caso["fipe"]) == caso["semelhanca"]


@pytest.mark.parametrize("caso", ler_casos("robots.json"), ids=lambda caso: caso["descricao"])
def test_robots(caso):
    assert pode_visitar(caso["robots"], caso["caminho"]) == caso["pode"]


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
