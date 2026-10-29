# Toda consulta à internet passa por aqui: o robô se identifica, espera entre
# duas consultas ao mesmo site e para de consultar um site que recusou. Nada é
# gravado em disco: a mesma consulta feita de novo na mesma sessão sai da
# memória, e some quando o R fecha. Nos testes, as respostas vêm de arquivos
# (variável VEICULOSBR_RESPOSTAS_GRAVADAS).

SEGUNDOS_ENTRE_CONSULTAS_AO_MESMO_SITE = c(
  "www.tabelafipebrasil.com" = 3,
  # O Parallelum aceita 50 consultas por minuto (cabeçalho x-throttle-limit); 1,5 s deixa em 40.
  "fipe.parallelum.com.br" = 1.5
)
SEGUNDOS_DE_ESPERA_DA_RESPOSTA = 30
TENTATIVAS = 2
SEGUNDOS_ANTES_DE_TENTAR_DE_NOVO = 2
# Site que disse "chega" (HTTP 429 ou 403) fica sem consulta por este tempo.
SEGUNDOS_DE_PAUSA_DEPOIS_DE_RECUSA = 600
APELIDO_DO_SITE = c("fipe.parallelum.com.br" = "parallelum", "www.tabelafipebrasil.com" = "tabelafipebrasil")

estado_da_rede = new.env(parent = emptyenv())
estado_da_rede$respostas_desta_sessao = list()
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

baixar = function(endereco, cabecalhos = list()) {
  pasta_gravadas = Sys.getenv("VEICULOSBR_RESPOSTAS_GRAVADAS")
  if (pasta_gravadas != "") {
    arquivo = file.path(pasta_gravadas, nome_do_arquivo_gravado(endereco))
    if (!file.exists(arquivo)) {
      stop(erro_de_consulta(
        paste0("Resposta n\u00e3o gravada para ", endereco, " (", basename(arquivo), ")"),
        "veiculosbr_resposta_nao_gravada"
      ))
    }
    texto = paste(readLines(arquivo, encoding = "UTF-8", warn = FALSE), collapse = "\n")
    return(list(status = 200L, texto = texto, cabecalhos = list()))
  }

  ja_consultada = estado_da_rede$respostas_desta_sessao[[endereco]]
  if (!is.null(ja_consultada)) {
    return(ja_consultada)
  }

  site = site_do_endereco(endereco)
  pausado_ate = estado_da_rede$pausado_ate[[site]]
  if (!is.null(pausado_ate) && agora() < pausado_ate) {
    minutos = max(1, round((pausado_ate - agora()) / 60))
    stop(erro_de_consulta(paste0(site, " recusou consultas h\u00e1 pouco; nova tentativa em ", minutos, " min")))
  }

  esperar_a_vez_do_site(site)
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

  # Só para quem desenvolve o pacote: VEICULOSBR_GRAVAR_RESPOSTAS guarda a resposta para os testes.
  pasta_para_gravar = Sys.getenv("VEICULOSBR_GRAVAR_RESPOSTAS")
  if (pasta_para_gravar != "") {
    dir.create(pasta_para_gravar, recursive = TRUE, showWarnings = FALSE)
    writeLines(enc2utf8(texto), file.path(pasta_para_gravar, nome_do_arquivo_gravado(endereco)), useBytes = TRUE)
  }

  resposta_guardada = list(status = 200L, texto = texto, cabecalhos = cabecalhos_da_resposta)
  estado_da_rede$respostas_desta_sessao[[endereco]] = resposta_guardada
  resposta_guardada
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

agora = function() {
  proc.time()[["elapsed"]]
}

esperar_a_vez_do_site = function(site) {
  intervalo = 0
  if (site %in% names(SEGUNDOS_ENTRE_CONSULTAS_AO_MESMO_SITE)) {
    intervalo = SEGUNDOS_ENTRE_CONSULTAS_AO_MESMO_SITE[[site]]
  }
  ultima = estado_da_rede$ultima_consulta[[site]]
  if (!is.null(ultima)) {
    falta = intervalo - (agora() - ultima)
    if (falta > 0) {
      Sys.sleep(falta)
    }
  }
  estado_da_rede$ultima_consulta[[site]] = agora()
}
