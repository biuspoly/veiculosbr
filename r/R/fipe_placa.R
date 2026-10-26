# Preço FIPE a partir da placa, com TODOS os candidatos quando houver dúvida.
# Mesmo caminho do pacote em Python (veja ?fipe_por_placa).

AVISO_GERAL = paste0(
  "Valor estimado a partir da placa: a identifica\u00e7\u00e3o do modelo pode estar errada. ",
  "Confira marca, modelo e ano-modelo antes de usar."
)
SEMELHANCA_MINIMA_DA_MARCA = 0.6
# O cadastro da placa e a FIPE descrevem cabine, tração e portas de jeitos diferentes, então
# a nota de quem é o certo pode ser baixa: valem todos os que ficam perto do melhor.
SEMELHANCA_MINIMA_DO_MODELO = 0.3
DISTANCIA_MAXIMA_ATE_O_MELHOR = 0.15
MAXIMO_DE_CANDIDATOS = 10
ORIGEM_BUSCA_NO_CATALOGO = "busca por semelhan\u00e7a no cat\u00e1logo FIPE"

#' Preço FIPE a partir da placa
#'
#' O caminho:
#' 1. a placa vai às fontes ([placa_consultar()]) e volta o veículo: marca,
#'    modelo, ano e, às vezes, os códigos FIPE que a fonte achou;
#' 2. com `conferir = TRUE`, cada código da fonte é procurado no catálogo FIPE
#'    no ano-modelo do veículo (o preço do catálogo vem com o mês de referência);
#' 3. se a fonte não trouxe nenhum código, o pacote procura no catálogo os
#'    modelos da mesma marca e ano com nome parecido ([semelhanca()]) e devolve
#'    todos os que ficam perto do melhor ([fipe_candidatos()]).
#'
#' Sem o ano-modelo (só o de fabricação), procura nos dois anos possíveis: o
#' veículo fabricado em 2017 pode ser modelo 2017 ou 2018. Sem o tipo (carro,
#' moto ou caminhão), escolhe o tipo em que a marca e o modelo mais se parecem.
#'
#' **O nome do modelo no cadastro da placa raramente é igual ao da FIPE.** Por
#' isso todo candidato diz de onde veio (`origem`), a `confianca` e a nota de
#' `semelhanca`, e os avisos dizem que o valor pode estar errado:
#' - `"alta"`: a fonte indicou um código só, e ele existe no catálogo no
#'   ano-modelo do veículo;
#' - `"media"`: a fonte indicou mais de um código, ou não deu para conferir;
#' - `"baixa"`: o código veio da busca por semelhança no catálogo.
#'
#' @param placa Uma placa.
#' @param fontes As fontes de placa, na ordem (veja [placa_consultar()]).
#' @param conferir Conferir no catálogo FIPE os códigos que a fonte indicou.
#' @param maximo_candidatos Quantos candidatos, no máximo, a busca por
#'   semelhança devolve.
#' @return Uma lista com `placa`, `veiculo` (`data.frame` de uma linha ou
#'   `NULL`), `candidatos` (`data.frame` com `codigo_fipe`, `modelo_fipe`,
#'   `ano_modelo`, `combustivel`, `preco`, `referencia`, `semelhanca`,
#'   `confianca`, `origem` e `conferido_no_catalogo`), `avisos` e `falhas`.
#' @source Veja a seção "De onde vêm os dados" em [veiculosbr].
#' @examples
#' \dontrun{
#' # Vai à internet
#' resultado = fipe_por_placa("ABC1D23")
#' resultado$veiculo
#' resultado$candidatos
#' resultado$avisos
#' }
#' @export
fipe_por_placa = function(placa, fontes = "tabelafipebrasil", conferir = TRUE,
                          maximo_candidatos = MAXIMO_DE_CANDIDATOS) {
  consulta = placa_consultar(placa, fontes)
  resultado = list(
    placa = placa_limpar(placa),
    veiculo = consulta$veiculo,
    candidatos = candidatos_vazios(),
    avisos = consulta$avisos,
    falhas = consulta$falhas
  )
  if (is.null(consulta$veiculo)) {
    resultado$avisos = c(resultado$avisos, "Placa n\u00e3o encontrada em nenhuma fonte.")
    return(resultado)
  }

  veiculo = consulta$veiculo
  resultado$avisos = c(AVISO_GERAL, resultado$avisos)

  anos_modelo = anos_modelo_possiveis(veiculo)
  if (is.na(veiculo$ano_modelo) && length(anos_modelo) > 0) {
    resultado$avisos = c(resultado$avisos, paste0(
      "A fonte n\u00e3o informou o ano-modelo: procurado em ", anos_modelo[1], " e ", anos_modelo[2],
      ", os dois poss\u00edveis para o ano de fabrica\u00e7\u00e3o."
    ))
  }

  resultado = tryCatch(
    {
      tipo_e_avisos = tipo_do_veiculo(veiculo)
      resultado$avisos = c(resultado$avisos, tipo_e_avisos$avisos)
      tipo = tipo_e_avisos$tipo
      if (!is.na(tipo)) {
        if (nrow(consulta$fipe) > 0) {
          da_fonte = candidatos_da_fonte(consulta, tipo, anos_modelo, conferir)
          resultado$candidatos = da_fonte$candidatos
          resultado$avisos = c(resultado$avisos, da_fonte$avisos)
        } else {
          for (ano_modelo in anos_modelo) {
            resultado$candidatos = rbind(
              resultado$candidatos,
              fipe_candidatos(tipo, veiculo$marca, veiculo$modelo, ano_modelo, veiculo$combustivel, maximo_candidatos)
            )
          }
          if (nrow(resultado$candidatos) == 0) {
            resultado$avisos = c(resultado$avisos, "Nenhum modelo parecido na tabela FIPE para esta marca e ano.")
          }
        }
      }
      resultado
    },
    veiculosbr_erro_consulta = function(erro) {
      resultado$falhas = c(resultado$falhas, paste0("cat\u00e1logo FIPE: ", conditionMessage(erro)))
      resultado
    }
  )

  if (nrow(resultado$candidatos) > 1) {
    resultado$avisos = c(resultado$avisos, paste0(
      nrow(resultado$candidatos), " pre\u00e7os da FIPE podem ser deste ve\u00edculo: todos est\u00e3o na lista."
    ))
  }
  rownames(resultado$candidatos) = NULL
  resultado
}

#' Modelos da FIPE parecidos com marca e modelo
#'
#' Procura no catálogo FIPE a marca mais parecida (nota mínima 0,6) e, dentro
#' dela, os modelos que existem no ano-modelo pedido. Devolve todos os que
#' ficam a até 0,15 da nota do melhor (e acima de `semelhanca_minima`), com o
#' preço de cada um. Todos com `confianca = "baixa"`.
#'
#' @param tipo `"carros"`, `"motos"` ou `"caminhoes"`.
#' @param marca,modelo Como aparecem no cadastro da placa.
#' @param ano_modelo O ano-modelo.
#' @param combustivel O combustível, se souber (ajuda a escolher o ano certo).
#' @param maximo_candidatos Quantos candidatos, no máximo.
#' @param semelhanca_minima A nota mínima de [semelhanca()].
#' @return Um `data.frame` com as colunas de candidatos de [fipe_por_placa()].
#' @source <https://fipe.parallelum.com.br/api/v2>.
#' @examples
#' \dontrun{
#' fipe_candidatos("motos", "HONDA", "CG 150 JOB", 2005, "Gasolina")
#' }
#' @export
fipe_candidatos = function(tipo, marca, modelo, ano_modelo, combustivel = NA,
                           maximo_candidatos = MAXIMO_DE_CANDIDATOS,
                           semelhanca_minima = SEMELHANCA_MINIMA_DO_MODELO) {
  if (is.na(ano_modelo)) {
    return(candidatos_vazios())
  }
  codigo_da_marca = codigo_da_marca(tipo, marca)
  if (is.na(codigo_da_marca)) {
    return(candidatos_vazios())
  }

  notas = numeric()
  codigos_do_modelo = character()
  nomes_do_modelo = character()
  codigos_do_ano = character()
  for (codigo_do_ano in codigos_de_ano_da_marca(tipo, codigo_da_marca, ano_modelo, combustivel)) {
    modelos = fipe_modelos_do_ano(tipo, codigo_da_marca, codigo_do_ano)
    if (nrow(modelos) == 0) {
      next
    }
    notas_do_ano = semelhanca(modelo, modelos$nome)
    parecidos = notas_do_ano >= semelhanca_minima
    notas = c(notas, notas_do_ano[parecidos])
    codigos_do_modelo = c(codigos_do_modelo, modelos$codigo[parecidos])
    nomes_do_modelo = c(nomes_do_modelo, modelos$nome[parecidos])
    codigos_do_ano = c(codigos_do_ano, rep(codigo_do_ano, sum(parecidos)))
  }
  if (length(notas) == 0) {
    return(candidatos_vazios())
  }

  # method = "radix": a mesma ordem de texto do Python, sem depender do idioma do computador.
  ordem = order(-notas, nomes_do_modelo, method = "radix")
  perto_do_melhor = notas[ordem] >= max(notas) - DISTANCIA_MAXIMA_ATE_O_MELHOR
  escolhidos = utils::head(ordem[perto_do_melhor], maximo_candidatos)

  candidatos = lapply(escolhidos, function(posicao) {
    preco = fipe_preco_do_modelo(tipo, codigo_da_marca, codigos_do_modelo[posicao], codigos_do_ano[posicao])
    if (nrow(preco) == 0) {
      return(NULL)
    }
    data.frame(
      codigo_fipe = preco$codigo_fipe,
      modelo_fipe = preco$modelo,
      ano_modelo = preco$ano_modelo,
      combustivel = preco$combustivel,
      preco = preco$preco,
      referencia = preco$referencia,
      semelhanca = notas[posicao],
      confianca = "baixa",
      origem = ORIGEM_BUSCA_NO_CATALOGO,
      conferido_no_catalogo = NA
    )
  })
  candidatos = Filter(Negate(is.null), candidatos)
  if (length(candidatos) == 0) candidatos_vazios() else do.call(rbind, candidatos)
}

candidatos_vazios = function() {
  data.frame(
    codigo_fipe = character(), modelo_fipe = character(), ano_modelo = integer(),
    combustivel = character(), preco = numeric(), referencia = character(), semelhanca = numeric(),
    confianca = character(), origem = character(), conferido_no_catalogo = logical()
  )
}

anos_modelo_possiveis = function(veiculo) {
  if (!is.na(veiculo$ano_modelo)) {
    return(veiculo$ano_modelo)
  }
  if (!is.na(veiculo$ano_fabricacao)) {
    return(c(veiculo$ano_fabricacao, veiculo$ano_fabricacao + 1L))
  }
  integer()
}

tipo_do_veiculo = function(veiculo) {
  tipo = tipo_pelo_segmento(veiculo$segmento)
  if (!is.na(tipo)) {
    return(list(tipo = tipo, avisos = character()))
  }
  if (length(palavras_do_nome(veiculo$segmento)) > 0) {
    aviso = paste0("A tabela FIPE n\u00e3o cobre este tipo de ve\u00edculo (", veiculo$segmento, ").")
    return(list(tipo = NA_character_, avisos = aviso))
  }

  pelo_catalogo = tipo_pelo_catalogo(veiculo$marca, veiculo$modelo)
  if (is.na(pelo_catalogo$tipo)) {
    aviso = paste0(
      "A fonte n\u00e3o disse o tipo do ve\u00edculo, e a marca e o modelo n\u00e3o aparecem ",
      "na tabela FIPE de carros, motos nem caminh\u00f5es."
    )
    return(list(tipo = NA_character_, avisos = aviso))
  }
  aviso = paste0(
    "A fonte n\u00e3o disse o tipo do ve\u00edculo: pela marca e pelo modelo, parece ",
    pelo_catalogo$tipo, " (semelhan\u00e7a ", pelo_catalogo$nota, ")."
  )
  list(tipo = pelo_catalogo$tipo, avisos = aviso)
}

tipo_pelo_catalogo = function(marca, modelo) {
  melhor_tipo = NA_character_
  melhor_nota = 0
  for (tipo in names(TIPO_NA_API)) {
    codigo = codigo_da_marca(tipo, marca)
    if (is.na(codigo)) {
      next
    }
    modelos = fipe_modelos(tipo, codigo)
    nota = if (nrow(modelos) == 0) 0 else max(semelhanca(modelo, modelos$nome))
    if (nota > melhor_nota) {
      melhor_tipo = tipo
      melhor_nota = nota
    }
  }
  if (melhor_nota < SEMELHANCA_MINIMA_DO_MODELO) {
    return(list(tipo = NA_character_, nota = melhor_nota))
  }
  list(tipo = melhor_tipo, nota = melhor_nota)
}

candidatos_da_fonte = function(consulta, tipo, anos_modelo, conferir) {
  veiculo = consulta$veiculo
  avisos = character()
  confianca_da_fonte = if (nrow(consulta$fipe) == 1 && length(anos_modelo) == 1) "alta" else "media"
  # Sem conferir, os dois anos possíveis dariam o mesmo preço da fonte duas vezes: fica um só.
  anos_a_conferir = if (conferir && length(anos_modelo) > 0) anos_modelo else veiculo$ano_modelo

  candidatos = list()
  for (linha in seq_len(nrow(consulta$fipe))) {
    fipe_da_fonte = consulta$fipe[linha, ]
    for (ano_modelo in anos_a_conferir) {
      candidato = data.frame(
        codigo_fipe = fipe_da_fonte$codigo_fipe,
        modelo_fipe = fipe_da_fonte$modelo,
        ano_modelo = as.integer(ano_modelo),
        combustivel = veiculo$combustivel,
        preco = fipe_da_fonte$preco,
        referencia = NA_character_,
        semelhanca = semelhanca(veiculo$modelo, fipe_da_fonte$modelo),
        confianca = confianca_da_fonte,
        origem = veiculo$fonte,
        conferido_no_catalogo = FALSE
      )
      if (conferir && !is.na(ano_modelo)) {
        preco_no_catalogo = preco_no_catalogo(tipo, fipe_da_fonte$codigo_fipe, ano_modelo, veiculo$combustivel)
        if (nrow(preco_no_catalogo) > 0) {
          candidato$preco = preco_no_catalogo$preco[1]
          candidato$referencia = preco_no_catalogo$referencia[1]
          candidato$combustivel = preco_no_catalogo$combustivel[1]
          candidato$conferido_no_catalogo = TRUE
        } else if (length(anos_a_conferir) == 1) {
          avisos = c(avisos, paste0(
            "O c\u00f3digo ", fipe_da_fonte$codigo_fipe, " n\u00e3o tem o ano-modelo ", ano_modelo,
            " no cat\u00e1logo FIPE: o pre\u00e7o \u00e9 o que a fonte mostrou."
          ))
        } else {
          next # dos dois anos possíveis, este não existe para o código
        }
      }
      if (!candidato$conferido_no_catalogo && candidato$confianca == "alta") {
        candidato$confianca = "media"
      }
      candidatos = c(candidatos, list(candidato))
    }
  }
  if (length(candidatos) == 0) {
    return(list(candidatos = candidatos_vazios(), avisos = avisos))
  }
  candidatos = do.call(rbind, candidatos)
  ano_para_ordenar = ifelse(is.na(candidatos$ano_modelo), 0L, candidatos$ano_modelo)
  ordem = order(-candidatos$semelhanca, candidatos$codigo_fipe, ano_para_ordenar, method = "radix")
  list(candidatos = candidatos[ordem, ], avisos = avisos)
}

preco_no_catalogo = function(tipo, codigo_fipe, ano_modelo, combustivel) {
  codigo_combustivel = codigo_do_combustivel(combustivel)
  anos = fipe_anos(tipo, codigo_fipe)
  anos_do_codigo = anos$codigo[sub("-.*$", "", anos$codigo) == as.character(ano_modelo)]
  ano_com_combustivel = paste0(ano_modelo, "-", codigo_combustivel)
  if (!is.na(codigo_combustivel) && ano_com_combustivel %in% anos_do_codigo) {
    anos_do_codigo = ano_com_combustivel
  }
  for (codigo_do_ano in anos_do_codigo) {
    precos = fipe_preco(tipo, codigo_fipe, codigo_do_ano)
    if (nrow(precos) > 0) {
      return(precos[1, ])
    }
  }
  tabela_de_precos_vazia()
}

codigo_da_marca = function(tipo, marca) {
  marcas = fipe_marcas(tipo)
  if (nrow(marcas) == 0) {
    return(NA_character_)
  }
  notas = semelhanca(marca, marcas$nome)
  # Empate: fica a primeira da lista, como no Python.
  melhor = which.max(notas)
  if (notas[melhor] >= SEMELHANCA_MINIMA_DA_MARCA) marcas$codigo[melhor] else NA_character_
}

codigos_de_ano_da_marca = function(tipo, codigo_da_marca, ano_modelo, combustivel) {
  anos = fipe_anos_da_marca(tipo, codigo_da_marca)
  do_ano = anos$codigo[sub("-.*$", "", anos$codigo) == as.character(ano_modelo)]
  codigo_combustivel = codigo_do_combustivel(combustivel)
  do_combustivel = do_ano[endsWith(do_ano, paste0("-", codigo_combustivel))]
  # Combustível que não bate com nenhum ano da marca: melhor procurar em todos do que em nenhum.
  if (length(do_combustivel) > 0) do_combustivel else do_ano
}
