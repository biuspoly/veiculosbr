# veiculosbr

Pacotes de dados de veículo brasileiros, **um em R e um em Python, com o mesmo comportamento**: placa
(antiga e Mercosul), RENAVAM, chassi e preço FIPE, inclusive a partir da placa. Projeto pessoal do
Marlon (biuspoly), parte do portfólio dele. O site de portfólio (`biuspoly/portfolio`, Shiny for Python,
dados sintéticos) é outro repositório e vai ganhar uma página que usa estes pacotes.

Origem: conversa de 26/10/2026 e o plano "Portar para o R" (22/10/2026, PDF do
usuário), em que placa e RENAVAM estão em "Utilidades brasileiras". O resumo do que foi decidido está em
`docs/origem.md` e o plano em `docs/plano.md`.

## Regras

- **Responder em português (PT-BR).** Código, nomes de função e documentação também em português.
- **Nada da empresa entra aqui.** O usuário trabalha num grupo de revendas, e o código de lá (Control,
  revendas, CNPJs, placas da frota, regras internas) não pode ser copiado. Tudo é escrito do zero, de forma
  genérica, e os testes usam dados inventados. Placa real só a de exemplo das documentações públicas.
- **R e Python dão a mesma resposta.** Os casos de teste moram uma vez só, em `casos/*.json`, e as duas
  suítes (testthat e pytest) leem esses arquivos. Uma regra mudou num lado e não mudou no outro = teste
  vermelho.
- **Fonte de dados só se permitir.** Respeitar o `robots.txt` e nunca contornar Cloudflare, captcha ou
  bloqueio. O placafipe.com bloqueia robôs em `/placa/` e protege a página com Cloudflare, então ele **não**
  é fonte. Cada fonte é um adaptador separado. Uma API paga entra pela chave que o próprio usuário informar.
- **FIPE pela placa pode estar errada, e o pacote diz isso.** Todo resultado traz de onde veio, o grau de
  confiança e TODOS os candidatos de FIPE quando houver mais de um, nunca só o "melhor".
- **Cota é escassa.** A busca por placa do Parallelum dá 5 consultas por mês sem token, 10 com o token
  gratuito e 500 no plano pago. O catálogo FIPE dá 1.000 consultas por dia. Por isso há cache local
  obrigatório, e os testes nunca gastam cota: respostas gravadas (httptest2 / respx).
- **Sem emoji em arquivo-fonte**, nem em comentário.
- Comentário enxuto: só o "porquê" que o código não diz.
