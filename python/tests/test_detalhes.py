"""O que não está nos casos compartilhados: leitores, rede e as cópias de dados/ e casos/."""

import filecmp
from pathlib import Path

import pytest

import veiculosbr
from veiculosbr import fipe_marcas, fipe_preco, rede
from veiculosbr.fipe import valor_em_reais
from veiculosbr.fontes_placa import ler_pagina_tabelafipebrasil, placa_consultar, tipo_pelo_segmento
from veiculosbr.rede import RespostaNaoGravada, baixar, nome_do_arquivo_gravado

RAIZ = Path(__file__).resolve().parents[2]


def test_valor_em_reais():
    assert valor_em_reais("R$ 257.276,00") == 257276.0
    assert valor_em_reais("R$ 7.191,50") == 7191.5
    assert valor_em_reais("") is None
    assert valor_em_reais(None) is None


def test_tipo_pelo_segmento():
    assert tipo_pelo_segmento("Auto") == "carros"
    assert tipo_pelo_segmento("Moto") == "motos"
    assert tipo_pelo_segmento("Caminhão") == "caminhoes"
    assert tipo_pelo_segmento("Outros") is None
    assert tipo_pelo_segmento(None) is None


def test_nome_do_arquivo_gravado():
    assert (nome_do_arquivo_gravado("https://fipe.parallelum.com.br/api/v2/cars/brands")
            == "parallelum_cars_brands")
    assert (nome_do_arquivo_gravado("https://www.tabelafipebrasil.com/placa/ZZA1B23")
            == "tabelafipebrasil_placa_ZZA1B23")


def test_resposta_que_nao_foi_gravada():
    with pytest.raises(RespostaNaoGravada):
        baixar("https://exemplo.invalido/nada")


def test_espera_entre_consultas_ao_mesmo_site(monkeypatch):
    esperas = []
    monkeypatch.setattr(rede.time, "sleep", esperas.append)
    monkeypatch.setattr(rede.time, "monotonic", lambda: 100.0)
    monkeypatch.setattr(rede, "_ultima_consulta_por_site", {})
    for site in ["fipe.parallelum.com.br", "www.tabelafipebrasil.com", "exemplo.invalido"]:
        rede._esperar_a_vez_do_site(site)
        rede._esperar_a_vez_do_site(site)
    assert esperas == [1.5, 3.0]


def test_pagina_sem_tabela_nao_acha_a_placa():
    assert ler_pagina_tabelafipebrasil("ZZE5F67", "<html><body>nada</body></html>") is None


def test_campos_lidos_da_pagina():
    consulta = placa_consultar("ZZB2C34")
    assert consulta.veiculo.modelo == "15.190 CRM 4X2 4P"
    assert consulta.veiculo.combustivel == "Diesel"
    assert consulta.veiculo.final_do_chassi == "Z000002"
    assert [fipe.codigo_fipe for fipe in consulta.fipe] == ["515134-1", "515151-1"]
    assert consulta.veiculo.fonte.startswith("tabelafipebrasil.com")


def test_placa_invalida_e_fonte_desconhecida():
    with pytest.raises(ValueError):
        placa_consultar("AB12")
    with pytest.raises(ValueError):
        placa_consultar("ZZA1B23", fontes=["outra"])


def test_catalogo():
    marcas = {marca.nome: marca.codigo for marca in fipe_marcas("caminhoes")}
    assert marcas["VOLKSWAGEN"] == "115"
    precos = fipe_preco("caminhoes", "515134-1", 2018)
    assert [(preco.ano_modelo, preco.preco) for preco in precos] == [(2018, 257276.0)]
    assert precos[0].fonte.startswith("Tabela FIPE, pela API do Parallelum")
    with pytest.raises(ValueError):
        fipe_marcas("barcos")


def test_tudo_exportado_existe():
    for nome in veiculosbr.__all__:
        assert hasattr(veiculosbr, nome), nome


@pytest.mark.parametrize("origem,copia", [
    (RAIZ / "dados", RAIZ / "python" / "src" / "veiculosbr" / "dados"),
    (RAIZ / "dados", RAIZ / "r" / "inst" / "extdata"),
    (RAIZ / "casos", RAIZ / "r" / "tests" / "testthat" / "casos"),
])
def test_copias_iguais(origem, copia):
    """Mudou dados/ ou casos/ e esqueceu de rodar ferramentas/sincronizar.py."""
    arquivos_na_origem = sorted(arquivo.relative_to(origem) for arquivo in origem.rglob("*") if arquivo.is_file())
    arquivos_na_copia = sorted(arquivo.relative_to(copia) for arquivo in copia.rglob("*") if arquivo.is_file())
    assert arquivos_na_origem == arquivos_na_copia
    for arquivo in arquivos_na_origem:
        assert filecmp.cmp(origem / arquivo, copia / arquivo, shallow=False), arquivo


@pytest.mark.parametrize("nome", ["README.md", "LICENSE"])
def test_arquivo_do_python_igual_ao_da_raiz(nome):
    assert filecmp.cmp(RAIZ / nome, RAIZ / "python" / nome, shallow=False)
