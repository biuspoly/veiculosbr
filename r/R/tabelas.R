# A tabela de faixas de placa por estado, que vem junto com o pacote (inst/extdata).
# Origem: Wikipédia em inglês, coletada em 26/10/2026 (veja ?veiculosbr).

tabelas_carregadas = new.env(parent = emptyenv())

faixas_uf = function() {
  if (is.null(tabelas_carregadas$faixas_uf)) {
    arquivo = system.file("extdata", "faixas_uf.csv", package = "veiculosbr", mustWork = TRUE)
    faixas = utils::read.csv(arquivo, encoding = "UTF-8", colClasses = "character", na.strings = character())
    faixas$numero_min = as.integer(faixas$numero_min)
    faixas$numero_max = as.integer(faixas$numero_max)
    tabelas_carregadas$faixas_uf = faixas
  }
  tabelas_carregadas$faixas_uf
}
