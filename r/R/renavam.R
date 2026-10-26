# RENAVAM: 11 dígitos, o último confere os 10 primeiros (módulo 11).
# O RENAVAM antigo tinha 9 dígitos; ele vale com dois zeros na frente.

PESOS_DO_RENAVAM = c(3, 2, 9, 8, 7, 6, 5, 4, 3, 2)

#' Conferir o RENAVAM
#'
#' `TRUE` quando o último dígito confere com os 10 primeiros (módulo 11). Aceita
#' pontuação e o RENAVAM antigo, de 9 dígitos (que ganha dois zeros na frente).
#' Isso só diz que o número está bem formado, não que existe um veículo com ele.
#'
#' @param renavam Vetor de números de RENAVAM (texto, com ou sem pontuação).
#' @return Vetor lógico do mesmo tamanho.
#' @examples
#' renavam_valido(c("94613459057", "946.134.590-57", "94613459058"))
#' @export
renavam_valido = function(renavam) {
  vapply(renavam_limpar(renavam), renavam_valido_um, logical(1), USE.NAMES = FALSE)
}

renavam_limpar = function(renavam) {
  renavam = ifelse(is.na(renavam), "", as.character(renavam))
  numeros = gsub("[^0-9]", "", renavam)
  antigos = nchar(numeros) == 9
  numeros[antigos] = paste0("00", numeros[antigos])
  numeros
}

renavam_digito = function(dez_primeiros_digitos) {
  digitos = as.integer(strsplit(dez_primeiros_digitos, "")[[1]])
  soma = sum(digitos * PESOS_DO_RENAVAM)
  resto = (soma * 10) %% 11
  if (resto == 10) 0L else as.integer(resto)
}

renavam_valido_um = function(numeros) {
  if (nchar(numeros) != 11 || numeros == "00000000000") {
    return(FALSE)
  }
  renavam_digito(substr(numeros, 1, 10)) == as.integer(substr(numeros, 11, 11))
}
