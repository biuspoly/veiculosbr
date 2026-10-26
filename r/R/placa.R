# Placa de veículo: a antiga (ABC1234) e a Mercosul (ABC1D23). Na conversão
# para a Mercosul, o 2º número vira letra: 0 = A, 1 = B ... 9 = J.

FORMATO_ANTIGO = "^[A-Z]{3}[0-9]{4}$"
FORMATO_MERCOSUL = "^[A-Z]{3}[0-9][A-Z][0-9]{2}$"
LETRAS_DO_QUINTO_CARACTERE = LETTERS[1:10]

#' Conferir, formatar e converter placas
#'
#' Todas aceitam um vetor de placas, com ou sem hífen, espaço ou letra
#' minúscula, e devolvem um vetor do mesmo tamanho (`NA` para a placa inválida).
#'
#' - `placa_valida()`: `TRUE` para o formato antigo ou o Mercosul.
#' - `placa_tipo()`: `"antiga"`, `"mercosul"` ou `NA`.
#' - `placa_para_mercosul()`: a antiga convertida (o 2º número vira letra, 0 = A
#'   ... 9 = J); a Mercosul volta igual.
#' - `placa_para_antiga()`: a que a Mercosul *teria* no formato antigo. Uma
#'   placa que já nasceu Mercosul nunca teve versão antiga; e só as letras de A
#'   a J têm número correspondente.
#' - `placa_formatar()`: a antiga com hífen (`ABC-1234`), a Mercosul sem
#'   (`ABC1D23`), como sai na placa.
#'
#' @param placa Vetor de placas.
#' @return Vetor do mesmo tamanho de `placa`.
#' @examples
#' placa_valida(c("ABC-1234", "ABC1D23", "AB12345"))
#' placa_para_mercosul("ABC1234")
#' placa_para_antiga("ABC1C34")
#' placa_formatar(c("abc1234", "abc1d23"))
#' @name placa
NULL

placa_limpar = function(placa) {
  placa = ifelse(is.na(placa), "", as.character(placa))
  gsub("[^A-Z0-9]", "", toupper(placa))
}

#' @rdname placa
#' @export
placa_tipo = function(placa) {
  placa = placa_limpar(placa)
  tipo = rep(NA_character_, length(placa))
  tipo[grepl(FORMATO_ANTIGO, placa)] = "antiga"
  tipo[grepl(FORMATO_MERCOSUL, placa)] = "mercosul"
  tipo
}

#' @rdname placa
#' @export
placa_valida = function(placa) {
  !is.na(placa_tipo(placa))
}

#' @rdname placa
#' @export
placa_para_mercosul = function(placa) {
  placa = placa_limpar(placa)
  tipo = placa_tipo(placa)
  convertida = rep(NA_character_, length(placa))

  e_mercosul = !is.na(tipo) & tipo == "mercosul"
  convertida[e_mercosul] = placa[e_mercosul]

  e_antiga = !is.na(tipo) & tipo == "antiga"
  segundo_numero = as.integer(substr(placa[e_antiga], 5, 5))
  convertida[e_antiga] = paste0(
    substr(placa[e_antiga], 1, 4),
    LETRAS_DO_QUINTO_CARACTERE[segundo_numero + 1],
    substr(placa[e_antiga], 6, 7)
  )
  convertida
}

#' @rdname placa
#' @export
placa_para_antiga = function(placa) {
  placa = placa_limpar(placa)
  tipo = placa_tipo(placa)
  convertida = rep(NA_character_, length(placa))

  e_antiga = !is.na(tipo) & tipo == "antiga"
  convertida[e_antiga] = placa[e_antiga]

  quinta_letra = substr(placa, 5, 5)
  tem_numero = !is.na(tipo) & tipo == "mercosul" & quinta_letra %in% LETRAS_DO_QUINTO_CARACTERE
  numero = match(quinta_letra[tem_numero], LETRAS_DO_QUINTO_CARACTERE) - 1
  convertida[tem_numero] = paste0(substr(placa[tem_numero], 1, 4), numero, substr(placa[tem_numero], 6, 7))
  convertida
}

#' @rdname placa
#' @export
placa_formatar = function(placa) {
  placa = placa_limpar(placa)
  tipo = placa_tipo(placa)
  formatada = rep(NA_character_, length(placa))

  e_antiga = !is.na(tipo) & tipo == "antiga"
  formatada[e_antiga] = paste0(substr(placa[e_antiga], 1, 3), "-", substr(placa[e_antiga], 4, 7))

  e_mercosul = !is.na(tipo) & tipo == "mercosul"
  formatada[e_mercosul] = placa[e_mercosul]
  formatada
}

#' Estado de origem da placa
#'
#' Cada estado recebeu faixas próprias de letras. O estado que sai daqui é
#' onde o veículo foi emplacado pela primeira vez, não onde está registrado
#' hoje. Faixa que a tabela não conhece (placa nova demais, ou inventada) dá
#' `NA`.
#'
#' @param placa Vetor de placas.
#' @return Vetor de siglas de estado (`"PR"`, `"SP"` ...) ou `NA`.
#' @source A tabela de faixas por estado da Wikipédia em inglês ("Vehicle
#'   registration plates of Brazil", que cita o Sinesp/Senatran), coletada em
#'   26/10/2026. Veja a seção "De onde vêm os dados" em [veiculosbr].
#' @examples
#' placa_uf(c("ABC1234", "PIA1B11", "MMN1234"))
#' @export
placa_uf = function(placa) {
  vapply(placa_limpar(placa), placa_uf_de_uma, character(1), USE.NAMES = FALSE)
}

placa_uf_de_uma = function(placa) {
  if (!placa_valida(placa)) {
    return(NA_character_)
  }
  letras = substr(placa, 1, 3)
  placa_antiga = placa_para_antiga(placa)
  # Sem o número (Mercosul com letra depois do J), decidem só as letras, se der um estado só.
  numero = if (is.na(placa_antiga)) NA_integer_ else as.integer(substr(placa_antiga, 4, 7))

  faixas = faixas_uf()
  dentro_das_letras = faixas$inicio <= letras & letras <= faixas$fim
  dentro_dos_numeros = is.na(numero) | (faixas$numero_min <= numero & numero <= faixas$numero_max)
  estados = unique(faixas$uf[dentro_das_letras & dentro_dos_numeros])
  if (length(estados) == 1) estados else NA_character_
}
