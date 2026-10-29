# Tabela FIPE pelo catálogo: marca, modelo, ano e preço, pela API pública do
# Parallelum (que repete os dados da FIPE).

ENDERECO_DA_API = "https://fipe.parallelum.com.br/api/v2"
FONTE_DO_CATALOGO = "Tabela FIPE, pela API do Parallelum (fipe.parallelum.com.br)"
TIPO_NA_API = c(carros = "cars", motos = "motorcycles", caminhoes = "trucks")
# Na FIPE, carro flex aparece como Gasolina (código 1).
CODIGO_DO_COMBUSTIVEL = c(GASOLINA = "1", FLEX = "1", ALCOOL = "2", ETANOL = "2", DIESEL = "3")

#' Tabela FIPE pelo catálogo
#'
#' Consultas à tabela da Fundação Instituto de Pesquisas Econômicas (FIPE)
#' pela API pública do Parallelum. Sem token, são 500 consultas por dia; com
#' o token gratuito de <https://fipe.api.br> na variável de ambiente
#' `VEICULOSBR_FIPE_TOKEN`, 1.000. Entre duas consultas, o pacote espera 1,5
#' segundo: o catálogo aceita até 50 por minuto. Nada é gravado em disco; a
#' mesma consulta feita de novo na mesma sessão não volta à internet.
#'
#' - `fipe_marcas()`: as marcas de um tipo de veículo.
#' - `fipe_modelos()`: os modelos de uma marca. O `codigo` é o do modelo no
#'   catálogo, não o código FIPE: o preço de todos sai de `fipe_precos_da_marca()`.
#' - `fipe_anos()`: os anos (com o combustível, ex. `2018-3`) de um código FIPE.
#' - `fipe_preco()`: o preço de um código FIPE num ano. `ano = 2018` traz todos
#'   os combustíveis daquele ano; `ano = "2018-3"` só aquele. O ano 32000 é a
#'   convenção da FIPE para o veículo zero quilômetro.
#' - `fipe_precos_da_marca()`: o preço de todos os modelos de uma marca num ano,
#'   com o código FIPE de cada um (o `ano` como em `fipe_preco()`). Faz uma
#'   consulta por modelo, mais uma ou duas: uma marca grande leva mais de um
#'   minuto e gasta uma boa parte da cota do dia.
#'
#' @param tipo `"carros"`, `"motos"` ou `"caminhoes"`.
#' @param marca O código da marca (coluna `codigo` de `fipe_marcas()`).
#' @param codigo_fipe O código FIPE, como `"515134-1"`.
#' @param ano Ano-modelo (`2018`) ou o código do ano com combustível (`"2018-3"`).
#' @return Um `data.frame`. Os de preço têm `codigo_fipe`, `marca`, `modelo`,
#'   `ano_modelo`, `combustivel`, `preco` (em reais), `referencia` (o mês da
#'   tabela) e `fonte`.
#' @source <https://fipe.parallelum.com.br/api/v2>, que repete a tabela de
#'   <https://veiculos.fipe.org.br>.
#' @examples
#' \dontrun{
#' # Vão à internet (API do Parallelum)
#' marcas = fipe_marcas("caminhoes")
#' fipe_preco("caminhoes", "515134-1", 2018)
#' fipe_precos_da_marca("motos", "80", 2005)
#' }
#' @name fipe
NULL

fipe_referencias = function() {
  lista = consultar_catalogo("/references")
  if (length(lista) == 0) {
    return(data.frame(codigo = character(), mes = character()))
  }
  data.frame(codigo = as.character(lista$code), mes = lista$month)
}

#' @rdname fipe
#' @export
fipe_marcas = function(tipo) {
  itens_do_catalogo(consultar_catalogo(paste0("/", tipo_na_api(tipo), "/brands")))
}

#' @rdname fipe
#' @export
fipe_modelos = function(tipo, marca) {
  itens_do_catalogo(consultar_catalogo(paste0("/", tipo_na_api(tipo), "/brands/", marca, "/models")))
}

fipe_anos_da_marca = function(tipo, marca) {
  itens_do_catalogo(consultar_catalogo(paste0("/", tipo_na_api(tipo), "/brands/", marca, "/years")))
}

fipe_modelos_do_ano = function(tipo, marca, ano) {
  caminho = paste0("/", tipo_na_api(tipo), "/brands/", marca, "/years/", ano, "/models")
  itens_do_catalogo(consultar_catalogo(caminho))
}

#' @rdname fipe
#' @export
fipe_anos = function(tipo, codigo_fipe) {
  itens_do_catalogo(consultar_catalogo(paste0("/", tipo_na_api(tipo), "/", codigo_fipe, "/years")))
}

#' @rdname fipe
#' @export
fipe_preco = function(tipo, codigo_fipe, ano) {
  codigos_do_ano = filtrar_codigos_do_ano(fipe_anos(tipo, codigo_fipe), ano)
  precos = lapply(codigos_do_ano, function(codigo_do_ano) {
    detalhe = consultar_catalogo(paste0("/", tipo_na_api(tipo), "/", codigo_fipe, "/years/", codigo_do_ano))
    preco_do_detalhe(detalhe)
  })
  juntar_precos(precos)
}

#' @rdname fipe
#' @export
fipe_precos_da_marca = function(tipo, marca, ano) {
  precos = list()
  for (codigo_do_ano in filtrar_codigos_do_ano(fipe_anos_da_marca(tipo, marca), ano)) {
    modelos = fipe_modelos_do_ano(tipo, marca, codigo_do_ano)
    for (modelo in modelos$codigo) {
      precos[[length(precos) + 1]] = fipe_preco_do_modelo(tipo, marca, modelo, codigo_do_ano)
    }
  }
  juntar_precos(precos)
}

# ano = 2018 fica com todos os combustíveis daquele ano; "2018-3", só com aquele.
filtrar_codigos_do_ano = function(anos, ano) {
  if (is.character(ano) && grepl("-", ano, fixed = TRUE)) {
    codigos = anos$codigo[anos$codigo == ano]
  } else {
    codigos = anos$codigo[sub("-.*$", "", anos$codigo) == as.character(ano)]
  }
  codigos
}

# O preço pelo código do modelo (não o código FIPE), como a busca de candidatos acha.
fipe_preco_do_modelo = function(tipo, marca, modelo, ano) {
  caminho = paste0("/", tipo_na_api(tipo), "/brands/", marca, "/models/", modelo, "/years/", ano)
  juntar_precos(list(preco_do_detalhe(consultar_catalogo(caminho))))
}

# "R$ 257.276,00" -> 257276
valor_em_reais = function(texto) {
  texto = ifelse(is.na(texto), "", as.character(texto))
  numeros = gsub("[^0-9,]", "", texto)
  valor = suppressWarnings(as.numeric(sub(",", ".", numeros, fixed = TRUE)))
  valor[numeros == ""] = NA_real_
  valor
}

codigo_do_combustivel = function(combustivel) {
  for (palavra in palavras_do_nome(combustivel)) {
    if (palavra %in% names(CODIGO_DO_COMBUSTIVEL)) {
      return(unname(CODIGO_DO_COMBUSTIVEL[palavra]))
    }
  }
  NA_character_
}

tabela_de_precos_vazia = function() {
  data.frame(
    codigo_fipe = character(), marca = character(), modelo = character(), ano_modelo = integer(),
    combustivel = character(), preco = numeric(), referencia = character(), fonte = character()
  )
}

preco_do_detalhe = function(detalhe) {
  if (length(detalhe) == 0 || is.null(detalhe$codeFipe)) {
    return(NULL)
  }
  data.frame(
    codigo_fipe = detalhe$codeFipe,
    marca = detalhe$brand,
    modelo = detalhe$model,
    ano_modelo = as.integer(detalhe$modelYear),
    combustivel = detalhe$fuel,
    preco = valor_em_reais(detalhe$price),
    referencia = detalhe$referenceMonth,
    fonte = FONTE_DO_CATALOGO
  )
}

juntar_precos = function(precos) {
  precos = Filter(Negate(is.null), precos)
  if (length(precos) == 0) {
    return(tabela_de_precos_vazia())
  }
  do.call(rbind, precos)
}

itens_do_catalogo = function(lista) {
  if (length(lista) == 0) {
    return(data.frame(codigo = character(), nome = character()))
  }
  data.frame(codigo = as.character(lista$code), nome = as.character(lista$name))
}

tipo_na_api = function(tipo) {
  if (length(tipo) != 1 || !(tipo %in% names(TIPO_NA_API))) {
    stop("tipo deve ser um destes: ", paste(names(TIPO_NA_API), collapse = ", "), " (veio ", tipo, ")", call. = FALSE)
  }
  unname(TIPO_NA_API[tipo])
}

consultar_catalogo = function(caminho) {
  token = Sys.getenv("VEICULOSBR_FIPE_TOKEN")
  cabecalhos = if (token != "") list("X-Subscription-Token" = token) else list()
  resposta = baixar(paste0(ENDERECO_DA_API, caminho), cabecalhos)
  if (resposta$status == 404L) {
    return(list())
  }
  jsonlite::fromJSON(resposta$texto, simplifyVector = TRUE)
}
