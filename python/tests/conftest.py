import json
from pathlib import Path

import pytest

PASTA_DOS_CASOS = Path(__file__).resolve().parents[2] / "casos"


def ler_casos(nome_do_arquivo: str) -> list[dict]:
    return json.loads((PASTA_DOS_CASOS / nome_do_arquivo).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def sem_internet(monkeypatch):
    """Os testes nunca vão à rede: leem casos/respostas."""
    monkeypatch.setenv("VEICULOSBR_RESPOSTAS_GRAVADAS", str(PASTA_DOS_CASOS / "respostas"))
    monkeypatch.delenv("VEICULOSBR_GRAVAR_RESPOSTAS", raising=False)
    monkeypatch.delenv("VEICULOSBR_FIPE_TOKEN", raising=False)
