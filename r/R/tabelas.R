# As tabelas de referência que vêm junto com o pacote (inst/extdata).
# Origem de cada uma: Wikipédia em inglês, coletada em 26/10/2026 (veja ?veiculosbr).

tabelas_carregadas = new.env(parent = emptyenv())

ler_tabela = function(nome_do_arquivo) {
  if (is.null(tabelas_carregadas[[nome_do_arquivo]])) {
    arquivo = system.file("extdata", nome_do_arquivo, package = "veiculosbr", mustWork = TRUE)
    tabela = utils::read.csv(arquivo, encoding = "UTF-8", colClasses = "character", na.strings = character())
    tabelas_carregadas[[nome_do_arquivo]] = tabela
  }
  tabelas_carregadas[[nome_do_arquivo]]
}

faixas_uf = function() {
  faixas = ler_tabela("faixas_uf.csv")
  faixas$numero_min = as.integer(faixas$numero_min)
  faixas$numero_max = as.integer(faixas$numero_max)
  faixas
}

pais_por_prefixo = function() {
  paises = ler_tabela("pais_chassi.csv")
  stats::setNames(paises$pais, paises$prefixo)
}

fabricante_por_codigo = function() {
  fabricantes = ler_tabela("fabricante_chassi.csv")
  stats::setNames(fabricantes$fabricante, fabricantes$codigo)
}
