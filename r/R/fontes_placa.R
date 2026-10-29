# De onde vêm os dados do veículo pela placa. Cada fonte é uma função à parte,
# com a mesma regra do pacote em Python (as fontes estão descritas em ?fipe_por_placa).

ENDERECO_TABELAFIPEBRASIL = "https://www.tabelafipebrasil.com/placa/"
ENDERECO_PARALLELUM_PLACA = "https://fipe.parallelum.com.br/api/v2/plates/"
FONTE_TABELAFIPEBRASIL = "tabelafipebrasil.com (p\u00e1gina p\u00fablica de placa)"
FONTE_PARALLELUM_PLACA = "Parallelum, busca por placa (fipe.parallelum.com.br)"
TEXTO_PLACA_NAO_ENCONTRADA = "placa n\u00e3o encontrada"
TIPO_PELO_SEGMENTO = c(AUTO = "carros", MOTO = "motos", CAMINHAO = "caminhoes")
FONTES_DE_PLACA = c("tabelafipebrasil", "parallelum")

# Tenta as fontes na ordem e para na primeira que achar a placa. Devolve
# veiculo (NULL se nenhuma achou), fipe (os códigos que a fonte mostrou),
# avisos e falhas. As fontes estão descritas em ?fipe_por_placa.
placa_consultar = function(placa, fontes = "tabelafipebrasil") {
  if (length(placa) != 1 || !placa_valida(placa)) {
    stop("Placa inv\u00e1lida: ", placa, call. = FALSE)
  }
  avisos = character()
  falhas = character()
  for (nome_da_fonte in fontes) {
    if (!(nome_da_fonte %in% FONTES_DE_PLACA)) {
      stop("Fonte desconhecida: ", nome_da_fonte, " (use ", paste(FONTES_DE_PLACA, collapse = ", "), ")", call. = FALSE)
    }
    consulta = tryCatch(
      if (nome_da_fonte == "tabelafipebrasil") consultar_tabelafipebrasil(placa) else consultar_parallelum(placa),
      veiculosbr_erro_consulta = function(erro) {
        falhas <<- c(falhas, paste0(nome_da_fonte, ": ", conditionMessage(erro)))
        "falhou"
      }
    )
    if (identical(consulta, "falhou")) {
      next
    }
    if (!is.null(consulta)) {
      avisos = c(avisos, consulta$avisos)
    }
    if (!is.null(consulta) && !is.null(consulta$veiculo)) {
      consulta$avisos = avisos
      consulta$falhas = falhas
      return(consulta)
    }
    falhas = c(falhas, paste0(nome_da_fonte, ": ", TEXTO_PLACA_NAO_ENCONTRADA))
  }
  list(veiculo = NULL, fipe = fipe_da_fonte_vazio(), avisos = avisos, falhas = falhas)
}

tipo_pelo_segmento = function(segmento) {
  palavras = palavras_do_nome(segmento)
  if (length(palavras) == 0 || !(palavras[1] %in% names(TIPO_PELO_SEGMENTO))) {
    return(NA_character_)
  }
  unname(TIPO_PELO_SEGMENTO[palavras[1]])
}

consultar_tabelafipebrasil = function(placa) {
  placa = placa_limpar(placa)
  resposta = baixar(paste0(ENDERECO_TABELAFIPEBRASIL, placa))
  if (resposta$status == 404L) {
    return(NULL)
  }
  ler_pagina_tabelafipebrasil(placa, resposta$texto)
}

ler_pagina_tabelafipebrasil = function(placa, html) {
  pagina = rvest::read_html(html)

  campos = list()
  for (linha in rvest::html_elements(pagina, "table.fipeTablePriceDetail tr")) {
    celulas = rvest::html_elements(linha, "td")
    if (length(celulas) == 2) {
      rotulo = paste(palavras_do_nome(rvest::html_text2(celulas[[1]])), collapse = " ")
      campos[[rotulo]] = trimws(rvest::html_text2(celulas[[2]]))
    }
  }
  if (length(campos) == 0) {
    return(NULL) # a página não achou a placa
  }

  veiculo = montar_veiculo(
    placa = placa,
    fonte = FONTE_TABELAFIPEBRASIL,
    marca = campos[["MARCA"]],
    modelo = campos[["MODELO"]],
    ano_fabricacao = numero_inteiro(campos[["ANO"]]),
    ano_modelo = numero_inteiro(campos[["ANO MODELO"]]),
    cor = campos[["COR"]],
    combustivel = campos[["COMBUSTIVEL"]],
    municipio = campos[["MUNICIPIO"]],
    uf = campos[["UF"]],
    segmento = campos[["SEGMENTO"]],
    final_do_chassi = final_do_chassi(campos[["CHASSI"]])
  )

  codigos = character()
  modelos = character()
  precos = numeric()
  for (linha in rvest::html_elements(pagina, "table.fipe-desktop tr")) {
    celulas = rvest::html_elements(linha, "td")
    classe_da_primeira = rvest::html_attr(celulas[1], "class")
    if (length(celulas) != 3 || (!is.na(classe_da_primeira) && grepl("fipeList", classe_da_primeira))) {
      next # a linha do cabeçalho
    }
    codigos = c(codigos, trimws(rvest::html_text2(celulas[[1]])))
    modelos = c(modelos, trimws(rvest::html_text2(celulas[[2]])))
    precos = c(precos, valor_em_reais(trimws(rvest::html_text2(celulas[[3]]))))
  }
  fipe = data.frame(codigo_fipe = codigos, modelo = modelos, preco = precos)
  list(veiculo = veiculo, fipe = fipe, avisos = character(), falhas = character())
}

consultar_parallelum = function(placa) {
  placa = placa_limpar(placa)
  token = Sys.getenv("VEICULOSBR_FIPE_TOKEN")
  cabecalhos = if (token != "") list("X-Subscription-Token" = token) else list()
  resposta = baixar(paste0(ENDERECO_PARALLELUM_PLACA, placa), cabecalhos)
  consulta = if (resposta$status == 404L) NULL else ler_resposta_parallelum(placa, resposta$texto)

  nomes_dos_cabecalhos = tolower(names(resposta$cabecalhos))
  restantes = resposta$cabecalhos[nomes_dos_cabecalhos == "x-plate-quota-remaining"]
  if (length(restantes) > 0) {
    if (is.null(consulta)) {
      consulta = list(veiculo = NULL, fipe = fipe_da_fonte_vazio(), avisos = character(), falhas = character())
    }
    consulta$avisos = c(consulta$avisos, paste0("Parallelum: restam ", restantes[[1]], " consultas de placa neste m\u00eas."))
  }
  consulta
}

ler_resposta_parallelum = function(placa, texto_json) {
  dados = jsonlite::fromJSON(texto_json, simplifyVector = TRUE)
  if (texto_vazio(dados$brand) && texto_vazio(dados$model)) {
    return(NULL)
  }
  veiculo = montar_veiculo(
    placa = placa,
    fonte = FONTE_PARALLELUM_PLACA,
    marca = dados$brand,
    modelo = dados$model,
    # A API devolve um ano só: o de fabricação, conferido contra o tabelafipebrasil.
    ano_fabricacao = numero_inteiro(dados$year),
    cor = dados$color,
    combustivel = dados$fuel,
    municipio = dados$city,
    uf = dados$state,
    segmento = dados$segment,
    final_do_chassi = final_do_chassi(dados$chassis)
  )
  precos_da_api = dados$fipePrices
  if (length(precos_da_api) == 0) {
    fipe = fipe_da_fonte_vazio()
  } else {
    fipe = data.frame(codigo_fipe = precos_da_api$codeFipe, modelo = precos_da_api$model, preco = valor_em_reais(precos_da_api$price))
  }
  list(veiculo = veiculo, fipe = fipe, avisos = character(), falhas = character())
}

montar_veiculo = function(placa, fonte, marca = NULL, modelo = NULL, ano_fabricacao = NA_integer_,
                          ano_modelo = NA_integer_, cor = NULL, combustivel = NULL, municipio = NULL,
                          uf = NULL, segmento = NULL, final_do_chassi = NA_character_) {
  data.frame(
    placa = placa,
    fonte = fonte,
    marca = texto_ou_na(marca),
    modelo = texto_ou_na(modelo),
    ano_fabricacao = ano_fabricacao,
    ano_modelo = ano_modelo,
    cor = texto_ou_na(cor),
    combustivel = texto_ou_na(combustivel),
    municipio = texto_ou_na(municipio),
    uf = texto_ou_na(uf),
    segmento = texto_ou_na(segmento),
    final_do_chassi = final_do_chassi
  )
}

fipe_da_fonte_vazio = function() {
  data.frame(codigo_fipe = character(), modelo = character(), preco = numeric())
}

texto_vazio = function(texto) {
  is.null(texto) || length(texto) == 0 || is.na(texto) || texto == ""
}

texto_ou_na = function(texto) {
  if (texto_vazio(texto)) NA_character_ else as.character(texto)
}

numero_inteiro = function(texto) {
  if (texto_vazio(texto)) {
    return(NA_integer_)
  }
  numeros = gsub("[^0-9]", "", texto)
  if (numeros == "") NA_integer_ else as.integer(numeros)
}

final_do_chassi = function(texto) {
  if (texto_vazio(texto)) {
    return(NA_character_)
  }
  final = gsub("[^A-Z0-9]", "", toupper(texto))
  if (final == "") NA_character_ else final
}
