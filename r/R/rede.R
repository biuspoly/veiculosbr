# Toda consulta à internet passa por aqui: o robô se identifica, espera entre
# duas consultas ao mesmo site, guarda as respostas num cache local e, nos
# testes, lê respostas gravadas em vez de ir à rede (VEICULOSBR_RESPOSTAS_GRAVADAS).

SEGUNDOS_ENTRE_CONSULTAS_AO_MESMO_SITE = 3
SEGUNDOS_DE_ESPERA_DA_RESPOSTA = 30
TENTATIVAS = 2
SEGUNDOS_ANTES_DE_TENTAR_DE_NOVO = 2
# Site que disse "chega" (HTTP 429 ou 403) fica sem consulta por este tempo.
SEGUNDOS_DE_PAUSA_DEPOIS_DE_RECUSA = 600

APELIDO_DO_SITE = c("fipe.parallelum.com.br" = "parallelum", "www.tabelafipebrasil.com" = "tabelafipebrasil")

estado_da_rede = new.env(parent = emptyenv())
estado_da_rede$ultima_consulta = list()
estado_da_rede$pausado_ate = list()

robo = function() {
  paste0("veiculosbr/", utils::packageVersion("veiculosbr"), " (+https://github.com/biuspoly/veiculosbr)")
}

erro_de_consulta = function(mensagem, classe = NULL) {
  structure(
    class = c(classe, "veiculosbr_erro_consulta", "error", "condition"),
    list(message = mensagem, call = NULL)
  )
}

# O mesmo nome do Python: o site (com apelido curto, para o caminho caber no limite
# de 100 caracteres do pacote) e o resto do endereço, sem o que não for letra, número,
# ponto ou hífen.
nome_do_arquivo_gravado = function(endereco) {
  sem_protocolo = sub("^https?://", "", endereco)
  site = sub("/.*$", "", sem_protocolo)
  caminho = if (grepl("/", sem_protocolo, fixed = TRUE)) sub("^[^/]*/", "", sem_protocolo) else ""
  if (site %in% names(APELIDO_DO_SITE)) {
    site = unname(APELIDO_DO_SITE[site])
  }
  caminho = sub("^api/v2/", "", caminho)
  gsub("[^A-Za-z0-9.-]", "_", paste0(site, "/", caminho))
}

site_do_endereco = function(endereco) {
  sub("^https?://([^/]+).*$", "\\1", endereco)
}

pasta_do_cache = function() {
  configurada = Sys.getenv("VEICULOSBR_CACHE")
  if (configurada == "0") {
    return(NULL)
  }
  if (configurada != "") {
    return(configurada)
  }
  tools::R_user_dir("veiculosbr", which = "cache")
}

#' Apaga o cache local
#'
#' As respostas das consultas ficam guardadas na pasta de cache do usuário
#' (`tools::R_user_dir("veiculosbr", "cache")`, ou a pasta da variável de
#' ambiente `VEICULOSBR_CACHE`; `VEICULOSBR_CACHE=0` desliga o cache): o
#' catálogo FIPE por 7 dias, as páginas de placa por 30.
#'
#' @return O número de arquivos apagados, invisível.
#' @export
limpar_cache = function() {
  pasta = pasta_do_cache()
  if (is.null(pasta) || !dir.exists(pasta)) {
    return(invisible(0L))
  }
  arquivos = list.files(pasta, full.names = TRUE)
  unlink(arquivos)
  invisible(length(arquivos))
}

ler_arquivo_de_texto = function(arquivo) {
  linhas = readLines(arquivo, encoding = "UTF-8", warn = FALSE)
  paste(linhas, collapse = "\n")
}

gravar_arquivo_de_texto = function(texto, arquivo) {
  dir.create(dirname(arquivo), recursive = TRUE, showWarnings = FALSE)
  writeLines(enc2utf8(texto), arquivo, useBytes = TRUE)
}

baixar = function(endereco, cabecalhos = list(), validade_cache_dias = 0, respeitar_ritmo = FALSE) {
  nome_gravado = nome_do_arquivo_gravado(endereco)

  pasta_gravadas = Sys.getenv("VEICULOSBR_RESPOSTAS_GRAVADAS")
  if (pasta_gravadas != "") {
    arquivo = file.path(pasta_gravadas, nome_gravado)
    if (!file.exists(arquivo)) {
      stop(erro_de_consulta(
        paste0("Resposta n\u00e3o gravada para ", endereco, " (", nome_gravado, ")"),
        "veiculosbr_resposta_nao_gravada"
      ))
    }
    return(list(status = 200L, texto = ler_arquivo_de_texto(arquivo), cabecalhos = list()))
  }

  arquivo_do_cache = arquivo_do_cache_valido(nome_gravado, validade_cache_dias)
  if (!is.null(arquivo_do_cache)) {
    return(list(status = 200L, texto = ler_arquivo_de_texto(arquivo_do_cache), cabecalhos = list()))
  }

  site = site_do_endereco(endereco)
  pausado_ate = estado_da_rede$pausado_ate[[site]]
  if (!is.null(pausado_ate) && agora() < pausado_ate) {
    minutos = max(1, round((pausado_ate - agora()) / 60))
    stop(erro_de_consulta(paste0(site, " recusou consultas h\u00e1 pouco; nova tentativa em ", minutos, " min")))
  }

  if (respeitar_ritmo) {
    esperar_a_vez_do_site(site)
  }

  resposta = consultar_com_nova_tentativa(endereco, cabecalhos)
  status = httr2::resp_status(resposta)
  texto = httr2::resp_body_string(resposta, encoding = "UTF-8")
  cabecalhos_da_resposta = as.list(httr2::resp_headers(resposta))

  if (status %in% c(403L, 429L)) {
    estado_da_rede$pausado_ate[[site]] = agora() + SEGUNDOS_DE_PAUSA_DEPOIS_DE_RECUSA
  }
  if (status == 429L) {
    stop(erro_de_consulta(
      paste0(site, " pediu para parar (HTTP 429: limite de consultas)"),
      "veiculosbr_cota_esgotada"
    ))
  }
  if (status == 403L) {
    stop(erro_de_consulta(paste0(site, " recusou a consulta (HTTP 403); costuma ser limite de consultas")))
  }
  if (status == 404L) {
    return(list(status = 404L, texto = texto, cabecalhos = cabecalhos_da_resposta))
  }
  if (status != 200L) {
    stop(erro_de_consulta(paste0(endereco, " respondeu HTTP ", status)))
  }

  # VEICULOSBR_GRAVAR_RESPOSTAS: consulta de verdade, guardada para os testes.
  pasta_para_gravar = Sys.getenv("VEICULOSBR_GRAVAR_RESPOSTAS")
  if (pasta_para_gravar != "") {
    gravar_arquivo_de_texto(texto, file.path(pasta_para_gravar, nome_gravado))
  }
  pasta = pasta_do_cache()
  if (validade_cache_dias > 0 && !is.null(pasta)) {
    gravar_arquivo_de_texto(texto, file.path(pasta, nome_gravado))
  }
  list(status = 200L, texto = texto, cabecalhos = cabecalhos_da_resposta)
}

consultar_com_nova_tentativa = function(endereco, cabecalhos) {
  pedido = httr2::request(endereco)
  pedido = httr2::req_user_agent(pedido, robo())
  if (length(cabecalhos) > 0) {
    pedido = do.call(httr2::req_headers, c(list(pedido), cabecalhos))
  }
  pedido = httr2::req_timeout(pedido, SEGUNDOS_DE_ESPERA_DA_RESPOSTA)
  pedido = httr2::req_error(pedido, is_error = function(resposta) FALSE)
  # Erro do lado do servidor (5xx) ou sem resposta: mais uma tentativa, 2 s depois.
  pedido = httr2::req_retry(
    pedido,
    max_tries = TENTATIVAS,
    retry_on_failure = TRUE,
    is_transient = function(resposta) httr2::resp_status(resposta) >= 500,
    backoff = function(tentativa) SEGUNDOS_ANTES_DE_TENTAR_DE_NOVO
  )
  tryCatch(
    httr2::req_perform(pedido),
    error = function(erro) {
      stop(erro_de_consulta(paste0("Sem resposta de ", endereco, ": ", conditionMessage(erro))))
    }
  )
}

arquivo_do_cache_valido = function(nome_gravado, validade_cache_dias) {
  pasta = pasta_do_cache()
  if (is.null(pasta) || validade_cache_dias <= 0) {
    return(NULL)
  }
  arquivo = file.path(pasta, nome_gravado)
  if (!file.exists(arquivo)) {
    return(NULL)
  }
  idade_em_dias = as.numeric(difftime(Sys.time(), file.mtime(arquivo), units = "days"))
  if (idade_em_dias <= validade_cache_dias) arquivo else NULL
}

agora = function() {
  proc.time()[["elapsed"]]
}

esperar_a_vez_do_site = function(site) {
  ultima = estado_da_rede$ultima_consulta[[site]]
  if (!is.null(ultima)) {
    falta = SEGUNDOS_ENTRE_CONSULTAS_AO_MESMO_SITE - (agora() - ultima)
    if (falta > 0) {
      Sys.sleep(falta)
    }
  }
  estado_da_rede$ultima_consulta[[site]] = agora()
}
