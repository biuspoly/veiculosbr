#' veiculosbr: placa, RENAVAM e preço FIPE de veículos brasileiros
#'
#' Confere e converte placas (antiga e Mercosul), confere o RENAVAM, consulta a
#' tabela FIPE e estima o preço FIPE a partir da placa, mostrando todos os
#' candidatos quando houver dúvida. A versão em Python (`pip install
#' veiculosbr`) tem as mesmas funções, com os mesmos nomes, e passa pelos
#' mesmos casos de teste.
#'
#' @section De onde vêm os dados:
#' **Nada aqui é dado oficial do Senatran, do Detran ou da FIPE consultado
#' direto na fonte.** Cada informação vem de um lugar:
#'
#' | Informação | Fonte | Quando |
#' |---|---|---|
#' | Faixa de letras de cada estado ([placa_uf()]) | Wikipédia em inglês, "Vehicle registration plates of Brazil", que cita o Sinesp/Senatran | coletada em 26/10/2026, vem dentro do pacote |
#' | Regras de placa e de RENAVAM | as regras públicas de formato (Resolução Contran 780/2019; módulo 11 do RENAVAM) | escritas no código |
#' | Tabela FIPE ([fipe_preco()] e afins) | API pública do Parallelum (<https://fipe.parallelum.com.br>), que repete a tabela de <https://veiculos.fipe.org.br> | consultada na hora |
#' | Veículo pela placa ([fipe_por_placa()]) | página pública <https://www.tabelafipebrasil.com/placa/>; e, só quando pedida, a busca por placa do Parallelum | consultada na hora |
#'
#' O cadastro da placa vem de sites que não são oficiais: se estiver errado ou
#' desatualizado lá, vem errado aqui. O nome do modelo no cadastro raramente é
#' igual ao da FIPE, por isso o preço pela placa é uma **estimativa** e vem
#' sempre com a fonte, a confiança e o aviso (veja [fipe_por_placa()]).
#'
#' Nada é gravado em disco: o pacote só consulta. A mesma consulta feita de
#' novo na mesma sessão do R não volta à internet.
#'
#' @section Boa conduta com os sites:
#' O pacote se identifica (`veiculosbr/<versão>` e o endereço do repositório),
#' espera 3 segundos entre consultas ao mesmo site e, quando um site recusa
#' (limite de consultas), fica 10 minutos sem consultá-lo.
#'
#' @section Variáveis de ambiente:
#' - `VEICULOSBR_FIPE_TOKEN`: o token gratuito de <https://fipe.api.br>, que
#'   aumenta o limite da API do Parallelum.
#' - `VEICULOSBR_RESPOSTAS_GRAVADAS`: usada pelos testes, lê as respostas de
#'   uma pasta em vez de ir à internet.
#'
#' @keywords internal
"_PACKAGE"
