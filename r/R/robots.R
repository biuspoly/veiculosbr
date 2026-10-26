# O site deixa este robô abrir a página? Lê o robots.txt (RFC 9309), com a
# mesma regra do pacote em Python: grupo com o nome do robô vale no lugar do
# "*", a regra mais longa ganha e, no empate, o Allow.

NOME_DO_ROBO = "veiculosbr"
VALIDADE_DO_ROBOTS_DIAS = 1

#' O robots.txt deixa abrir este caminho?
#'
#' @param texto_do_robots O conteúdo do robots.txt do site.
#' @param caminho O caminho da página, com a consulta (ex.: `/placa/ABC1D23`).
#' @param nome_do_robo O nome com que o robô se identifica.
#' @return `TRUE` ou `FALSE`.
#' @examples
#' pode_visitar("User-agent: *\nDisallow: /placa/", "/placa/ABC1D23")
#' @export
pode_visitar = function(texto_do_robots, caminho, nome_do_robo = NOME_DO_ROBO) {
  grupos = regras_por_grupo(texto_do_robots, nome_do_robo)
  regras = if (!is.null(grupos$para_o_robo)) grupos$para_o_robo else grupos$para_todos
  if (length(regras) == 0) {
    return(TRUE)
  }

  melhor_tamanho = -1
  permitido = TRUE
  for (regra in regras) {
    if (!caminho_casa(regra$padrao, caminho)) {
      next
    }
    tamanho = nchar(regra$padrao)
    if (tamanho > melhor_tamanho || (tamanho == melhor_tamanho && regra$tipo == "allow")) {
      melhor_tamanho = tamanho
      permitido = regra$tipo == "allow"
    }
  }
  permitido
}

site_permite = function(endereco) {
  inicio_do_site = sub("^(https?://[^/]+).*$", "\\1", endereco)
  resposta = baixar(paste0(inicio_do_site, "/robots.txt"), validade_cache_dias = VALIDADE_DO_ROBOTS_DIAS)
  if (resposta$status != 200L) {
    return(TRUE) # sem robots.txt, o site não pôs regra
  }
  caminho = sub("^https?://[^/]+", "", endereco)
  if (caminho == "") {
    caminho = "/"
  }
  pode_visitar(resposta$texto, caminho)
}

regras_por_grupo = function(texto_do_robots, nome_do_robo) {
  para_o_robo = NULL
  para_todos = list()
  robos_do_grupo = character()
  lendo_robos = FALSE

  for (linha in strsplit(texto_do_robots, "\r?\n")[[1]]) {
    linha = trimws(sub("#.*$", "", linha))
    if (!grepl(":", linha, fixed = TRUE)) {
      next
    }
    campo = tolower(trimws(sub(":.*$", "", linha)))
    valor = trimws(sub("^[^:]*:", "", linha))

    if (campo == "user-agent") {
      if (!lendo_robos) {
        robos_do_grupo = character()
      }
      robos_do_grupo = c(robos_do_grupo, tolower(valor))
      lendo_robos = TRUE
      next
    }

    lendo_robos = FALSE
    if (!(campo %in% c("allow", "disallow")) || valor == "") {
      next
    }
    regra = list(tipo = campo, padrao = valor)
    if (tolower(nome_do_robo) %in% robos_do_grupo) {
      para_o_robo = c(para_o_robo, list(regra))
    }
    if ("*" %in% robos_do_grupo) {
      para_todos = c(para_todos, list(regra))
    }
  }
  list(para_o_robo = para_o_robo, para_todos = para_todos)
}

caminho_casa = function(padrao, caminho) {
  ancorado_no_fim = endsWith(padrao, "$")
  if (ancorado_no_fim) {
    padrao = substr(padrao, 1, nchar(padrao) - 1)
  }
  pedacos = strsplit(padrao, "*", fixed = TRUE)[[1]]
  pedacos_escapados = gsub("([][{}()+*^$|\\\\?.])", "\\\\\\1", pedacos)
  expressao = paste0("^", paste(pedacos_escapados, collapse = ".*"))
  if (ancorado_no_fim) {
    # "*" no fim seguido de "$" ("/x*$") volta como pedaço vazio que strsplit descarta.
    if (endsWith(padrao, "*")) {
      expressao = paste0(expressao, ".*")
    }
    expressao = paste0(expressao, "$")
  }
  grepl(expressao, caminho, perl = TRUE)
}
