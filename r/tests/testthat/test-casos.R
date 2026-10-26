# Os casos de casos/*.json: os mesmos que o pacote em Python confere.

test_that("placa", {
  for (caso in ler_casos("placa.json")) {
    placa = ou_na(caso$placa)
    rotulo = paste("placa", placa)
    expect_identical(placa_valida(placa), caso$valida, label = rotulo)
    expect_identical(placa_tipo(placa), ou_na(caso$tipo), label = rotulo)
    expect_identical(placa_para_mercosul(placa), ou_na(caso$mercosul), label = rotulo)
    expect_identical(placa_para_antiga(placa), ou_na(caso$antiga), label = rotulo)
    expect_identical(placa_formatar(placa), ou_na(caso$formatada), label = rotulo)
    expect_identical(placa_uf(placa), ou_na(caso$uf), label = rotulo)
  }
})

test_that("RENAVAM", {
  for (caso in ler_casos("renavam.json")) {
    renavam = ou_na(caso$renavam)
    rotulo = paste("RENAVAM", renavam)
    expect_identical(renavam_limpar(renavam), caso$limpo, label = rotulo)
    expect_identical(renavam_valido(renavam), caso$valido, label = rotulo)
  }
})

test_that("semelhan\u00e7a", {
  for (caso in ler_casos("semelhanca.json")) {
    rotulo = paste(caso$placa, "~", caso$fipe)
    expect_equal(semelhanca(ou_na(caso$placa), caso$fipe), caso$semelhanca, label = rotulo)
  }
})

test_that("FIPE pela placa", {
  for (caso in ler_casos("fipe_por_placa.json")) {
    rotulo = caso$descricao
    resultado = fipe_por_placa(caso$placa, fontes = unlist(caso$fontes), conferir = caso$conferir)

    expect_identical(!is.null(resultado$veiculo), caso$encontrou, label = rotulo)
    if (caso$encontrou) {
      expect_identical(resultado$veiculo$marca, caso$marca, label = rotulo)
      expect_identical(resultado$veiculo$ano_modelo, ou_na(caso$ano_modelo_do_veiculo, NA_integer_), label = rotulo)
    }

    candidatos = resultado$candidatos
    expect_identical(nrow(candidatos), length(caso$candidatos), label = rotulo)
    for (posicao in seq_along(caso$candidatos)) {
      esperado = caso$candidatos[[posicao]]
      expect_identical(candidatos$codigo_fipe[posicao], esperado$codigo_fipe, label = rotulo)
      expect_identical(candidatos$ano_modelo[posicao], ou_na(esperado$ano_modelo, NA_integer_), label = rotulo)
      expect_equal(candidatos$preco[posicao], esperado$preco, label = rotulo)
      expect_identical(candidatos$confianca[posicao], esperado$confianca, label = rotulo)
      expect_identical(candidatos$conferido_no_catalogo[posicao], ou_na(esperado$conferido_no_catalogo, NA), label = rotulo)
      expect_identical(candidatos$referencia[posicao], ou_na(esperado$referencia), label = rotulo)
    }

    todos_os_avisos = paste(resultado$avisos, collapse = " | ")
    for (trecho in caso$aviso_contem) {
      expect_true(grepl(trecho, todos_os_avisos, fixed = TRUE), label = paste(rotulo, "- aviso:", trecho))
    }
    todas_as_falhas = paste(resultado$falhas, collapse = " | ")
    for (trecho in caso$falha_contem) {
      expect_true(grepl(trecho, todas_as_falhas, fixed = TRUE), label = paste(rotulo, "- falha:", trecho))
    }
  }
})
