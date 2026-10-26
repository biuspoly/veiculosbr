# Chassi (VIN): 17 caracteres, sem I, O e Q (norma ISO 3779). Os 2 primeiros
# dizem o país, os 3 primeiros o fabricante, o 10º o ano-modelo.

FORMATO_DO_CHASSI = "^[A-HJ-NPR-Z0-9]{17}$"
# 30 códigos de ano: A = 1980 ... Y = 2000, 1 = 2001 ... 9 = 2009, e o ciclo recomeça em 2010.
CODIGOS_DE_ANO = strsplit("ABCDEFGHJKLMNPRSTVWXY123456789", "")[[1]]
VALOR_DA_LETRA = c(
  A = 1, B = 2, C = 3, D = 4, E = 5, F = 6, G = 7, H = 8, J = 1, K = 2, L = 3, M = 4, N = 5,
  P = 7, R = 9, S = 2, T = 3, U = 4, V = 5, W = 6, X = 7, Y = 8, Z = 9
)
PESOS_DO_DIGITO_9 = c(8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)

#' Conferir e ler o chassi
#'
#' - `chassi_limpar()`: só letras maiúsculas e números.
#' - `chassi_valido()`: 17 caracteres, sem I, O e Q. O 9º caractere não é
#'   conferido: ele só é dígito verificador obrigatório na América do Norte e
#'   na China (veja `chassi_digito9_confere()`).
#' - `chassi_pais()`: o país, pelos 2 primeiros caracteres.
#' - `chassi_fabricante()`: o fabricante, pelos 3 primeiros. Só os fabricantes
#'   com fábrica no Brasil estão na tabela, com o nome como a fonte escreve
#'   (em inglês).
#' - `chassi_ano_modelo()`: o ano-modelo pelo 10º caractere. O código se repete
#'   a cada 30 anos (A = 1980 ou 2010): fica o mais recente que não passe de
#'   `ano_referencia + 1`. Nem todo fabricante segue esse padrão.
#' - `chassi_digito9_confere()`: confere o 9º caractere pela regra da América
#'   do Norte.
#'
#' @param chassi Vetor de chassis.
#' @param ano_referencia O ano de hoje, ou outro, para escolher o ciclo de 30 anos.
#' @return Vetor do mesmo tamanho de `chassi`.
#' @source País e fabricante: Wikipédia em inglês ("Vehicle identification
#'   number"), coletada em 26/10/2026. Veja a seção "De onde vêm os dados" em
#'   [veiculosbr].
#' @examples
#' chassi_valido("9BWZZZ377VT004251")
#' chassi_pais("9BWZZZ377VT004251")
#' chassi_fabricante("9BWZZZ377VT004251")
#' chassi_ano_modelo("9BWZZZ377VT004251", ano_referencia = 2000)
#' chassi_digito9_confere("1M8GDM9AXKP042788")
#' @name chassi
NULL

#' @rdname chassi
#' @export
chassi_limpar = function(chassi) {
  chassi = ifelse(is.na(chassi), "", as.character(chassi))
  gsub("[^A-Z0-9]", "", toupper(chassi))
}

#' @rdname chassi
#' @export
chassi_valido = function(chassi) {
  grepl(FORMATO_DO_CHASSI, chassi_limpar(chassi))
}

#' @rdname chassi
#' @export
chassi_pais = function(chassi) {
  chassi = chassi_limpar(chassi)
  paises = pais_por_prefixo()
  pelos_dois = unname(paises[substr(chassi, 1, 2)])
  pelo_primeiro = unname(paises[substr(chassi, 1, 1)])
  pais = ifelse(is.na(pelos_dois), pelo_primeiro, pelos_dois)
  pais[!chassi_valido(chassi)] = NA_character_
  pais
}

#' @rdname chassi
#' @export
chassi_fabricante = function(chassi) {
  chassi = chassi_limpar(chassi)
  fabricante = unname(fabricante_por_codigo()[substr(chassi, 1, 3)])
  fabricante[!chassi_valido(chassi)] = NA_character_
  fabricante
}

#' @rdname chassi
#' @export
chassi_ano_modelo = function(chassi, ano_referencia = as.integer(format(Sys.Date(), "%Y"))) {
  chassi = chassi_limpar(chassi)
  vapply(chassi, chassi_ano_modelo_de_um, integer(1), ano_referencia = ano_referencia, USE.NAMES = FALSE)
}

chassi_ano_modelo_de_um = function(chassi, ano_referencia) {
  codigo_do_ano = substr(chassi, 10, 10)
  if (!chassi_valido(chassi) || !(codigo_do_ano %in% CODIGOS_DE_ANO)) {
    return(NA_integer_)
  }
  posicao = match(codigo_do_ano, CODIGOS_DE_ANO) - 1
  anos_possiveis = 1980 + posicao + 30 * (0:3)
  anos_que_cabem = anos_possiveis[anos_possiveis <= ano_referencia + 1]
  if (length(anos_que_cabem) == 0) NA_integer_ else as.integer(max(anos_que_cabem))
}

#' @rdname chassi
#' @export
chassi_digito9_confere = function(chassi) {
  vapply(chassi_limpar(chassi), chassi_digito9_confere_de_um, logical(1), USE.NAMES = FALSE)
}

chassi_digito9_confere_de_um = function(chassi) {
  if (!chassi_valido(chassi)) {
    return(FALSE)
  }
  caracteres = strsplit(chassi, "")[[1]]
  valores = ifelse(grepl("[0-9]", caracteres), suppressWarnings(as.integer(caracteres)), VALOR_DA_LETRA[caracteres])
  resto = sum(valores * PESOS_DO_DIGITO_9) %% 11
  digito_esperado = if (resto == 10) "X" else as.character(resto)
  caracteres[9] == digito_esperado
}
