# Quanto o nome do modelo na placa parece com o nome na tabela FIPE (0 a 1).
# Mesma conta do pacote em Python, conferida pelos mesmos casos de teste.

PESO_DA_COBERTURA = 0.8
PESO_DA_SOBREPOSICAO = 0.2
PARECENCA_MINIMA_ENTRE_PALAVRAS = 0.75
NOTA_DE_ABREVIACAO = 0.9
LETRAS_COM_ACENTO = "\u00e1\u00e0\u00e2\u00e3\u00e4\u00e9\u00e8\u00ea\u00eb\u00ed\u00ec\u00ee\u00ef\u00f3\u00f2\u00f4\u00f5\u00f6\u00fa\u00f9\u00fb\u00fc\u00e7\u00f1\u00c1\u00c0\u00c2\u00c3\u00c4\u00c9\u00c8\u00ca\u00cb\u00cd\u00cc\u00ce\u00cf\u00d3\u00d2\u00d4\u00d5\u00d6\u00da\u00d9\u00db\u00dc\u00c7\u00d1"
LETRAS_SEM_ACENTO = "aaaaaeeeeiiiiooooouuuucnAAAAAEEEEIIIIOOOOOUUUUCN"

palavras_do_nome = function(nome) {
  if (length(nome) == 0 || is.na(nome)) {
    return(character())
  }
  sem_acento = chartr(LETRAS_COM_ACENTO, LETRAS_SEM_ACENTO, enc2utf8(as.character(nome)))
  so_letras_e_numeros = trimws(gsub("[^A-Z0-9]+", " ", toupper(sem_acento)))
  if (so_letras_e_numeros == "") character() else strsplit(so_letras_e_numeros, " ", fixed = TRUE)[[1]]
}

parecenca_entre_palavras = function(palavra_placa, palavra_fipe) {
  if (palavra_placa == palavra_fipe) {
    return(1)
  }
  alguma_tem_numero = grepl("[0-9]", palavra_placa) || grepl("[0-9]", palavra_fipe)
  if (alguma_tem_numero || nchar(palavra_placa) < 3 || nchar(palavra_fipe) < 3) {
    return(0)
  }
  if (startsWith(palavra_fipe, palavra_placa) || startsWith(palavra_placa, palavra_fipe)) {
    return(NOTA_DE_ABREVIACAO)
  }
  # adist: quantas letras trocar, tirar ou pôr para uma palavra virar a outra (Levenshtein).
  distancia = utils::adist(palavra_placa, palavra_fipe)[1, 1]
  parecenca = 1 - distancia / max(nchar(palavra_placa), nchar(palavra_fipe))
  if (parecenca >= PARECENCA_MINIMA_ENTRE_PALAVRAS) parecenca else 0
}

#' Semelhança entre o nome do modelo na placa e o nome na FIPE
#'
#' O cadastro da placa e a FIPE escrevem o mesmo veículo de jeitos diferentes
#' ("15.190 CRM 4X2" e "15-190 E Constellation 2p"), então a comparação é por
#' palavra: quantas palavras da placa aparecem no nome da FIPE (cobertura, peso
#' 0,8) e quanto as duas listas se sobrepõem (peso 0,2). Número só vale igual;
#' palavra de 3 letras ou mais aceita abreviação (nota 0,9) e erro pequeno de
#' digitação. Acento e maiúscula não contam.
#'
#' @param nome_na_placa,nome_na_fipe Textos a comparar (vetores do mesmo
#'   tamanho, ou um deles de tamanho 1).
#' @return Vetor de notas de 0 a 1, com 3 casas.
#' @examples
#' semelhanca("CG 125 CARGO", "CG 125 CARGO/ CARGO KS/125i CARGO")
#' modelos_da_fipe = c("15-190 E Worker 2p (diesel)(E5)", "17-190 E Worker 2p (diesel)(E5)")
#' semelhanca("15.190 CRM 4X2 4P", modelos_da_fipe)
#' @export
semelhanca = function(nome_na_placa, nome_na_fipe) {
  mapply(semelhanca_de_um_par, nome_na_placa, nome_na_fipe, USE.NAMES = FALSE)
}

semelhanca_de_um_par = function(nome_na_placa, nome_na_fipe) {
  palavras_placa = palavras_do_nome(nome_na_placa)
  palavras_fipe = palavras_do_nome(nome_na_fipe)
  if (length(palavras_placa) == 0 || length(palavras_fipe) == 0) {
    return(0)
  }

  notas = vapply(palavras_placa, function(palavra) {
    max(vapply(palavras_fipe, function(outra) parecenca_entre_palavras(palavra, outra), numeric(1)))
  }, numeric(1))
  cobertura = mean(notas)

  em_comum = intersect(palavras_placa, palavras_fipe)
  todas = union(palavras_placa, palavras_fipe)
  sobreposicao = length(em_comum) / length(todas)

  round(PESO_DA_COBERTURA * cobertura + PESO_DA_SOBREPOSICAO * sobreposicao, 3)
}
