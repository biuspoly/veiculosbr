#' veiculosbr: placa, RENAVAM, chassi e preço FIPE de veículos brasileiros
#'
#' Confere e converte placas (antiga e Mercosul), confere RENAVAM e chassi,
#' consulta a tabela FIPE e estima o preço FIPE a partir da placa, mostrando
#' todos os candidatos quando houver dúvida. A versão em Python
#' (`pip install veiculosbr`) tem as mesmas funções, com os mesmos nomes, e
#' passa pelos mesmos casos de teste.
#'
#' @section De onde vêm os dados:
#' **Nada aqui é dado oficial do Senatran, do Detran ou da FIPE consultado
#' direto na fonte.** Cada informação vem de um lugar:
#'
#' | Informação | Fonte | Atualização |
#' |---|---|---|
#' | Faixa de letras de cada estado ([placa_uf()]) | Wikipédia em inglês, "Vehicle registration plates of Brazil", que cita o Sinesp/Senatran | coletada em 26/10/2026, vem dentro do pacote |
#' | País e fabricante do chassi ([chassi_pais()], [chassi_fabricante()]) | Wikipédia em inglês, "Vehicle identification number" | coletada em 26/10/2026, vem dentro do pacote |
#' | Regras de placa, RENAVAM e chassi | as regras públicas de formato (Resolução Contran 780/2019, módulo 11 do RENAVAM, norma ISO 3779) | escritas no código |
#' | Tabela FIPE ([fipe_preco()] e afins) | API pública do Parallelum (<https://fipe.parallelum.com.br>), que repete a tabela de <https://veiculos.fipe.org.br> | consulta na hora, cache de 7 dias |
#' | Veículo pela placa ([placa_consultar()]) | página pública <https://www.tabelafipebrasil.com/placa/>; e, só quando pedida, a busca por placa do Parallelum | consulta na hora, cache de 30 dias |
#'
#' O cadastro da placa vem de sites que não são oficiais: se estiver errado ou
#' desatualizado lá, vem errado aqui. O nome do modelo no cadastro raramente é
#' igual ao da FIPE, por isso o preço pela placa é uma **estimativa** e vem
#' sempre com a fonte, a confiança e o aviso (veja [fipe_por_placa()]).
#'
#' @section Boa conduta com os sites:
#' O pacote se identifica como robô (`veiculosbr/<versão>` e o endereço do
#' repositório), confere o `robots.txt` antes de ler uma página, espera 3
#' segundos entre consultas ao mesmo site, guarda as respostas em cache e,
#' quando um site recusa (limite de consultas), fica 10 minutos sem
#' consultá-lo. Sites que bloqueiam robôs não são usados.
#'
#' @section Variáveis de ambiente:
#' - `VEICULOSBR_FIPE_TOKEN`: o token gratuito de <https://fipe.api.br>, que
#'   aumenta o limite da API do Parallelum.
#' - `VEICULOSBR_CACHE`: outra pasta para o cache; `0` desliga.
#' - `VEICULOSBR_RESPOSTAS_GRAVADAS`: usada pelos testes, lê as respostas de
#'   uma pasta em vez de ir à internet.
#'
#' @keywords internal
"_PACKAGE"
