"""Preço FIPE a partir da placa, com TODOS os candidatos quando houver dúvida.

O caminho:
1. a placa vai às fontes (fontes_placa.py) e volta o veículo: marca, modelo,
   ano e, às vezes, os códigos FIPE que a fonte achou;
2. com conferir=True, cada código da fonte é procurado no catálogo FIPE no
   ano-modelo do veículo (o preço do catálogo vem com o mês de referência);
3. se a fonte não trouxe nenhum código, o pacote procura no catálogo os modelos
   da mesma marca e ano com nome parecido (semelhanca.py) e devolve todos.

Sem o ano-modelo (só o de fabricação), procura nos dois anos possíveis: o carro
fabricado em 2017 pode ser modelo 2017 ou 2018. Sem o tipo (carro, moto ou
caminhão), escolhe o tipo em que a marca e o modelo mais se parecem.

O nome do modelo no cadastro da placa raramente é igual ao da FIPE. Por isso
todo resultado diz de onde veio, a confiança e o aviso: pode estar errado.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .fipe import (
    TIPO_NA_API,
    PrecoFipe,
    codigo_do_combustivel,
    fipe_anos,
    fipe_anos_da_marca,
    fipe_marcas,
    fipe_modelos,
    fipe_modelos_do_ano,
    fipe_preco,
    fipe_preco_do_modelo,
)
from .fontes_placa import FONTES_PADRAO, Veiculo, placa_consultar, tipo_pelo_segmento
from .placa import placa_limpar
from .rede import ErroDeConsulta
from .semelhanca import palavras_do_nome, semelhanca

AVISO_GERAL = ("Valor estimado a partir da placa: a identificação do modelo pode estar errada. "
               "Confira marca, modelo e ano-modelo antes de usar.")
SEMELHANCA_MINIMA_DA_MARCA = 0.6
# O cadastro da placa e a FIPE descrevem cabine, tração e portas de jeitos diferentes, então
# a nota de quem é o certo pode ser baixa: valem todos os que ficam perto do melhor.
SEMELHANCA_MINIMA_DO_MODELO = 0.3
DISTANCIA_MAXIMA_ATE_O_MELHOR = 0.15
MAXIMO_DE_CANDIDATOS = 10
ORIGEM_BUSCA_NO_CATALOGO = "busca por semelhança no catálogo FIPE"


@dataclass
class CandidatoFipe:
    codigo_fipe: str
    modelo_fipe: str
    ano_modelo: int | None
    combustivel: str | None
    preco: float | None
    referencia: str | None
    semelhanca: float
    confianca: str            # alta, media ou baixa
    origem: str               # quem indicou este código
    conferido_no_catalogo: bool | None  # None: veio do próprio catálogo

    def para_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResultadoFipePorPlaca:
    placa: str
    veiculo: Veiculo | None
    candidatos: list[CandidatoFipe] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    falhas: list[str] = field(default_factory=list)


def fipe_por_placa(placa, fontes=FONTES_PADRAO, conferir: bool = True,
                   maximo_candidatos: int = MAXIMO_DE_CANDIDATOS) -> ResultadoFipePorPlaca:
    consulta = placa_consultar(placa, fontes)
    resultado = ResultadoFipePorPlaca(placa=placa_limpar(placa), veiculo=consulta.veiculo,
                                      avisos=list(consulta.avisos), falhas=list(consulta.falhas))
    if consulta.veiculo is None:
        resultado.avisos.append("Placa não encontrada em nenhuma fonte.")
        return resultado

    veiculo = consulta.veiculo
    resultado.avisos.insert(0, AVISO_GERAL)

    anos_modelo = _anos_modelo_possiveis(veiculo)
    if veiculo.ano_modelo is None and anos_modelo:
        resultado.avisos.append(f"A fonte não informou o ano-modelo: procurado em {anos_modelo[0]} e "
                                f"{anos_modelo[1]}, os dois possíveis para o ano de fabricação.")

    try:
        tipo = _tipo_do_veiculo(veiculo, resultado)
        if tipo is None:
            return resultado
        if consulta.fipe:
            resultado.candidatos = _candidatos_da_fonte(consulta, tipo, anos_modelo, conferir, resultado)
        else:
            for ano_modelo in anos_modelo:
                resultado.candidatos += fipe_candidatos(tipo, veiculo.marca, veiculo.modelo, ano_modelo,
                                                        veiculo.combustivel, maximo_candidatos)
            if not resultado.candidatos:
                resultado.avisos.append("Nenhum modelo parecido na tabela FIPE para esta marca e ano.")
    except ErroDeConsulta as erro:
        resultado.falhas.append(f"catálogo FIPE: {erro}")

    if len(resultado.candidatos) > 1:
        resultado.avisos.append(f"{len(resultado.candidatos)} preços da FIPE podem ser deste veículo: "
                                "todos estão na lista.")
    return resultado


def fipe_candidatos(tipo: str, marca, modelo, ano_modelo: int | None, combustivel=None,
                    maximo_candidatos: int = MAXIMO_DE_CANDIDATOS,
                    semelhanca_minima: float = SEMELHANCA_MINIMA_DO_MODELO) -> list[CandidatoFipe]:
    """Os modelos do catálogo FIPE parecidos com marca + modelo, no ano-modelo pedido."""
    if ano_modelo is None:
        return []
    codigo_da_marca = _codigo_da_marca(tipo, marca)
    if codigo_da_marca is None:
        return []

    parecidos = []
    for codigo_do_ano in _codigos_de_ano_da_marca(tipo, codigo_da_marca, ano_modelo, combustivel):
        for modelo_fipe in fipe_modelos_do_ano(tipo, codigo_da_marca, codigo_do_ano):
            nota = semelhanca(modelo, modelo_fipe.nome)
            if nota >= semelhanca_minima:
                parecidos.append((nota, modelo_fipe, codigo_do_ano))
    parecidos.sort(key=lambda parecido: (-parecido[0], parecido[1].nome))
    if parecidos:
        nota_do_melhor = parecidos[0][0]
        parecidos = [parecido for parecido in parecidos
                     if parecido[0] >= nota_do_melhor - DISTANCIA_MAXIMA_ATE_O_MELHOR]

    candidatos = []
    for nota, modelo_fipe, codigo_do_ano in parecidos[:maximo_candidatos]:
        preco = fipe_preco_do_modelo(tipo, codigo_da_marca, modelo_fipe.codigo, codigo_do_ano)
        if preco is None:
            continue
        candidatos.append(CandidatoFipe(
            codigo_fipe=preco.codigo_fipe, modelo_fipe=preco.modelo, ano_modelo=preco.ano_modelo,
            combustivel=preco.combustivel, preco=preco.preco, referencia=preco.referencia,
            semelhanca=nota, confianca="baixa", origem=ORIGEM_BUSCA_NO_CATALOGO,
            conferido_no_catalogo=None,
        ))
    return candidatos


def _anos_modelo_possiveis(veiculo: Veiculo) -> list[int]:
    if veiculo.ano_modelo is not None:
        return [veiculo.ano_modelo]
    if veiculo.ano_fabricacao is not None:
        return [veiculo.ano_fabricacao, veiculo.ano_fabricacao + 1]
    return []


def _tipo_do_veiculo(veiculo: Veiculo, resultado: ResultadoFipePorPlaca) -> str | None:
    tipo = tipo_pelo_segmento(veiculo.segmento)
    if tipo is not None:
        return tipo
    if palavras_do_nome(veiculo.segmento):
        resultado.avisos.append(f"A tabela FIPE não cobre este tipo de veículo ({veiculo.segmento}).")
        return None

    tipo, nota = _tipo_pelo_catalogo(veiculo.marca, veiculo.modelo)
    if tipo is None:
        resultado.avisos.append("A fonte não disse o tipo do veículo, e a marca e o modelo não aparecem "
                                "na tabela FIPE de carros, motos nem caminhões.")
        return None
    resultado.avisos.append(f"A fonte não disse o tipo do veículo: pela marca e pelo modelo, parece "
                            f"{tipo} (semelhança {nota}).")
    return tipo


def _tipo_pelo_catalogo(marca, modelo) -> tuple[str | None, float]:
    melhor_tipo, melhor_nota = None, 0.0
    for tipo in TIPO_NA_API:
        codigo_da_marca = _codigo_da_marca(tipo, marca)
        if codigo_da_marca is None:
            continue
        nota = max((semelhanca(modelo, modelo_fipe.nome) for modelo_fipe in fipe_modelos(tipo, codigo_da_marca)),
                   default=0.0)
        if nota > melhor_nota:
            melhor_tipo, melhor_nota = tipo, nota
    if melhor_nota < SEMELHANCA_MINIMA_DO_MODELO:
        return None, melhor_nota
    return melhor_tipo, melhor_nota


def _candidatos_da_fonte(consulta, tipo, anos_modelo, conferir, resultado) -> list[CandidatoFipe]:
    veiculo = consulta.veiculo
    confianca_da_fonte = "alta" if len(consulta.fipe) == 1 and len(anos_modelo) == 1 else "media"
    # Sem conferir, os dois anos possíveis dariam o mesmo preço da fonte duas vezes: fica um só.
    anos_a_conferir = anos_modelo if conferir and anos_modelo else [veiculo.ano_modelo]
    candidatos = []
    for fipe_da_fonte in consulta.fipe:
        for ano_modelo in anos_a_conferir:
            candidato = CandidatoFipe(
                codigo_fipe=fipe_da_fonte.codigo_fipe, modelo_fipe=fipe_da_fonte.modelo,
                ano_modelo=ano_modelo, combustivel=veiculo.combustivel, preco=fipe_da_fonte.preco,
                referencia=None, semelhanca=semelhanca(veiculo.modelo, fipe_da_fonte.modelo),
                confianca=confianca_da_fonte, origem=veiculo.fonte, conferido_no_catalogo=False,
            )
            if conferir and ano_modelo is not None:
                preco_no_catalogo = _preco_no_catalogo(tipo, fipe_da_fonte.codigo_fipe, ano_modelo,
                                                       veiculo.combustivel)
                if preco_no_catalogo is not None:
                    candidato.preco = preco_no_catalogo.preco
                    candidato.referencia = preco_no_catalogo.referencia
                    candidato.combustivel = preco_no_catalogo.combustivel
                    candidato.conferido_no_catalogo = True
                elif len(anos_a_conferir) == 1:
                    resultado.avisos.append(f"O código {fipe_da_fonte.codigo_fipe} não tem o ano-modelo "
                                            f"{ano_modelo} no catálogo FIPE: o preço é o que a fonte mostrou.")
                else:
                    continue  # dos dois anos possíveis, este não existe para o código
            if not candidato.conferido_no_catalogo and candidato.confianca == "alta":
                candidato.confianca = "media"
            candidatos.append(candidato)
    candidatos.sort(key=lambda candidato: (-candidato.semelhanca, candidato.codigo_fipe,
                                           candidato.ano_modelo or 0))
    return candidatos


def _preco_no_catalogo(tipo, codigo_fipe, ano_modelo, combustivel) -> PrecoFipe | None:
    codigo_combustivel = codigo_do_combustivel(combustivel)
    anos_do_codigo = [item.codigo for item in fipe_anos(tipo, codigo_fipe)
                      if item.codigo.split("-")[0] == str(ano_modelo)]
    if codigo_combustivel and f"{ano_modelo}-{codigo_combustivel}" in anos_do_codigo:
        anos_do_codigo = [f"{ano_modelo}-{codigo_combustivel}"]
    for codigo_do_ano in anos_do_codigo:
        precos = fipe_preco(tipo, codigo_fipe, codigo_do_ano)
        if precos:
            return precos[0]
    return None


def _codigo_da_marca(tipo, marca) -> str | None:
    melhor_nota, melhor_codigo = 0.0, None
    for marca_fipe in fipe_marcas(tipo):
        nota = semelhanca(marca, marca_fipe.nome)
        if nota > melhor_nota:
            melhor_nota, melhor_codigo = nota, marca_fipe.codigo
    return melhor_codigo if melhor_nota >= SEMELHANCA_MINIMA_DA_MARCA else None


def _codigos_de_ano_da_marca(tipo, codigo_da_marca, ano_modelo, combustivel) -> list[str]:
    do_ano = [item.codigo for item in fipe_anos_da_marca(tipo, codigo_da_marca)
              if item.codigo.split("-")[0] == str(ano_modelo)]
    codigo_combustivel = codigo_do_combustivel(combustivel)
    do_combustivel = [codigo for codigo in do_ano if codigo.endswith(f"-{codigo_combustivel}")]
    # Combustível que não bate com nenhum ano da marca: melhor procurar em todos do que em nenhum.
    return do_combustivel or do_ano
