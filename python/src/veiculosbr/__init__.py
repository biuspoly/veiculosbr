"""veiculosbr: placa (antiga e Mercosul), RENAVAM, chassi e preço FIPE, inclusive pela placa.

De onde vêm os dados: veja o README (seção "De onde vêm os dados") e dados/LEIAME.md.
"""

from .chassi import (
    chassi_ano_modelo,
    chassi_digito9_confere,
    chassi_fabricante,
    chassi_limpar,
    chassi_pais,
    chassi_valido,
)
from .fipe import (
    PrecoFipe,
    fipe_anos,
    fipe_anos_da_marca,
    fipe_marcas,
    fipe_modelos,
    fipe_modelos_do_ano,
    fipe_preco,
    fipe_preco_do_modelo,
    fipe_referencias,
    valor_em_reais,
)
from .fipe_placa import AVISO_GERAL, CandidatoFipe, ResultadoFipePorPlaca, fipe_candidatos, fipe_por_placa
from .fontes_placa import ConsultaDePlaca, FipeDaFonte, Veiculo, placa_consultar
from .placa import (
    placa_formatar,
    placa_limpar,
    placa_para_antiga,
    placa_para_mercosul,
    placa_tipo,
    placa_uf,
    placa_valida,
)
from .rede import VERSAO as __version__
from .rede import CotaEsgotada, ErroDeConsulta, limpar_cache
from .renavam import renavam_digito, renavam_limpar, renavam_valido
from .robots import pode_visitar
from .semelhanca import semelhanca

__all__ = [
    "AVISO_GERAL", "CandidatoFipe", "ConsultaDePlaca", "CotaEsgotada", "ErroDeConsulta", "FipeDaFonte",
    "PrecoFipe", "ResultadoFipePorPlaca", "Veiculo", "__version__",
    "chassi_ano_modelo", "chassi_digito9_confere", "chassi_fabricante", "chassi_limpar", "chassi_pais",
    "chassi_valido",
    "fipe_anos", "fipe_anos_da_marca", "fipe_candidatos", "fipe_marcas", "fipe_modelos",
    "fipe_modelos_do_ano", "fipe_por_placa", "fipe_preco", "fipe_preco_do_modelo", "fipe_referencias",
    "limpar_cache",
    "placa_consultar", "placa_formatar", "placa_limpar", "placa_para_antiga", "placa_para_mercosul",
    "placa_tipo", "placa_uf", "placa_valida", "pode_visitar",
    "renavam_digito", "renavam_limpar", "renavam_valido",
    "semelhanca", "valor_em_reais",
]
