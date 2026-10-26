# Os testes nunca vão à rede: leem casos/respostas.
withr::local_envvar(
  VEICULOSBR_RESPOSTAS_GRAVADAS = normalizePath(testthat::test_path("casos", "respostas")),
  VEICULOSBR_GRAVAR_RESPOSTAS = NA,
  VEICULOSBR_FIPE_TOKEN = NA,
  .local_envir = testthat::teardown_env()
)

ler_casos = function(nome_do_arquivo) {
  jsonlite::fromJSON(testthat::test_path("casos", nome_do_arquivo), simplifyVector = FALSE)
}

# null do JSON vira NA, para comparar com o que as funções devolvem.
ou_na = function(valor, tipo = NA_character_) {
  if (is.null(valor)) tipo else valor
}
