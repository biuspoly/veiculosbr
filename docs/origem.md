# De onde veio

Resumo da conversa de 26/10/2026 em que o projeto começou, para que o trabalho aqui continue sem ela.

## Os repositórios

- `biuspoly/portfolio` (04/09/2026): o site de portfólio em Shiny for Python, com dados sintéticos.
- `biuspoly/veiculosbr` (este): os pacotes. Repositório separado do site, porque um pacote publicado no
  CRAN, no r-universe e no PyPI vive melhor no seu próprio repositório. O site ganha uma página de
  demonstração que usa os pacotes.

## O que o usuário pediu

> [...] a criação de pacotes e bibliotecas tanto em R como Python (caso não exista, e se existir, algo
> melhor e mais completo) [...]: a placa do Mercosul, tanto conferência como troca, conferir RENAVAM, e o
> principal, o FIPE, usando a API do Parallelum e um FIPE por placa (deixando claro que pode haver erros),
> extraindo as informações de sites como placafipe e outros (se aparecer mais de um FIPE, mostrar todos).

Placa e RENAVAM estavam num plano maior de utilidades brasileiras; este repositório tira a parte de veículo
para um pacote próprio. CNPJ com letras e feriados por estado ficam para outro pacote.

## O que se descobriu

- **A API v2 do Parallelum tem busca por placa** (`GET /api/v2/plates/{placa}`, "Alpha"), que devolve o
  veículo e a lista `fipePrices`. A cota é de 5 consultas por mês sem token, 10 com o token gratuito e 500
  no plano pago (cabeçalhos `X-Plate-Quota-Limit` e `X-Plate-Quota-Remaining`). O token vai no cabeçalho
  `X-Subscription-Token`. O teste com a placa de exemplo (ABC1D23) voltou Passat 1979 de Curitiba com
  `fipePrices` vazio.
- O catálogo FIPE do Parallelum: o número visto foi 1.000 consultas por dia sem token. Em 29/10/2026, a
  documentação (<https://fipe.api.br/docs/api>) e o cabeçalho `x-ratelimit-limit` diziam 500 sem token e
  1.000 com ele, mais 50 por minuto (`x-throttle-limit`).
- O **placafipe.com** bloqueia robôs em `/placa/` no `robots.txt` e responde 403 com o desafio do
  Cloudflare. Não é fonte.
- Os nomes `veiculosbr`, `veiculobr`, `placabr`, `fipebr` e `frotabr` estavam livres no PyPI, no CRAN e no
  r-universe.
