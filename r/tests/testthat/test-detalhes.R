# O que não está nos casos compartilhados: leitores e rede.

test_that("valor em reais", {
  expect_identical(valor_em_reais("R$ 257.276,00"), 257276)
  expect_identical(valor_em_reais("R$ 7.191,50"), 7191.5)
  expect_identical(valor_em_reais(""), NA_real_)
  expect_identical(valor_em_reais(NA), NA_real_)
})

test_that("tipo pelo segmento", {
  expect_identical(tipo_pelo_segmento("Auto"), "carros")
  expect_identical(tipo_pelo_segmento("Moto"), "motos")
  expect_identical(tipo_pelo_segmento("Caminh\u00e3o"), "caminhoes")
  expect_identical(tipo_pelo_segmento("Outros"), NA_character_)
  expect_identical(tipo_pelo_segmento(NA), NA_character_)
})

test_that("nome do arquivo gravado igual ao do Python", {
  expect_identical(
    nome_do_arquivo_gravado("https://fipe.parallelum.com.br/api/v2/cars/brands"),
    "parallelum_cars_brands"
  )
  expect_identical(
    nome_do_arquivo_gravado("https://www.tabelafipebrasil.com/robots.txt"),
    "tabelafipebrasil_robots.txt"
  )
})

test_that("resposta que n\u00e3o foi gravada vira erro de consulta", {
  expect_error(baixar("https://exemplo.invalido/nada"), class = "veiculosbr_resposta_nao_gravada")
})

test_that("p\u00e1gina sem a tabela n\u00e3o acha a placa", {
  expect_null(ler_pagina_tabelafipebrasil("ZZE5F67", "<html><body>nada</body></html>"))
})

test_that("campos lidos da p\u00e1gina", {
  consulta = placa_consultar("ZZB2C34")
  expect_identical(consulta$veiculo$modelo, "15.190 CRM 4X2 4P")
  expect_identical(consulta$veiculo$combustivel, "Diesel")
  expect_identical(consulta$veiculo$final_do_chassi, "Z000002")
  expect_identical(consulta$fipe$codigo_fipe, c("515134-1", "515151-1"))
  expect_true(startsWith(consulta$veiculo$fonte, "tabelafipebrasil.com"))
})

test_that("placa inv\u00e1lida e fonte desconhecida", {
  expect_error(placa_consultar("AB12"), "Placa inv")
  expect_error(placa_consultar("ZZA1B23", fontes = "outra"), "Fonte desconhecida")
})

test_that("cat\u00e1logo", {
  marcas = fipe_marcas("caminhoes")
  expect_identical(marcas$codigo[marcas$nome == "VOLKSWAGEN"], "115")
  precos = fipe_preco("caminhoes", "515134-1", 2018)
  expect_identical(precos$ano_modelo, 2018L)
  expect_identical(precos$preco, 257276)
  expect_true(startsWith(precos$fonte, "Tabela FIPE, pela API do Parallelum"))
  expect_error(fipe_marcas("barcos"), "tipo deve ser")
})

test_that("fun\u00e7\u00f5es de placa aceitam vetor", {
  expect_identical(placa_valida(c("ABC1234", "x", NA)), c(TRUE, FALSE, FALSE))
  expect_identical(placa_uf(c("ABC1234", "PIA1B11")), c("PR", "PI"))
  expect_identical(renavam_valido(c("94613459057", "1")), c(TRUE, FALSE))
})
