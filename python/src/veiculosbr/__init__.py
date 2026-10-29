"""veiculosbr: placa (antiga e Mercosul), RENAVAM e preço FIPE, inclusive pela placa.

De onde vêm os dados: veja o README (seção "De onde vêm os dados") e dados/LEIAME.md.
"""

from .fipe import PrecoFipe, fipe_anos, fipe_marcas, fipe_modelos, fipe_preco, fipe_precos_da_marca
from .fipe_placa import CandidatoFipe, ResultadoFipePorPlaca, fipe_candidatos, fipe_por_placa
from .fontes_placa import Veiculo
from .placa import placa_formatar, placa_para_antiga, placa_para_mercosul, placa_tipo, placa_uf, placa_valida
from .rede import VERSAO as __version__
from .rede import CotaEsgotada, ErroDeConsulta
from .renavam import renavam_valido

__all__ = [
    "CandidatoFipe", "CotaEsgotada", "ErroDeConsulta", "PrecoFipe", "ResultadoFipePorPlaca", "Veiculo",
    "__version__",
    "fipe_anos", "fipe_candidatos", "fipe_marcas", "fipe_modelos", "fipe_por_placa", "fipe_preco",
    "fipe_precos_da_marca",
    "placa_formatar", "placa_para_antiga", "placa_para_mercosul", "placa_tipo", "placa_uf", "placa_valida",
    "renavam_valido",
]
