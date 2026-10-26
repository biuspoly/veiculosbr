# veiculosbr

Pacotes de dados de veículo brasileiros, **um em R e um em Python, com o mesmo comportamento**: placa
(antiga e Mercosul), RENAVAM, chassi e preço FIPE, inclusive a partir da placa. Projeto pessoal do
Marlon (biuspoly), parte do portfólio dele. O site de portfólio (`biuspoly/portfolio`, Shiny for Python,
dados sintéticos) é outro repositório e vai ganhar uma página que usa estes pacotes.

Origem e decisões: `docs/origem.md` (a conversa de 26/10/2026) e `docs/plano.md` (o estado atual, as fontes
aceitas e recusadas, as dependências). O README é o que o usuário do pacote lê.

## Estrutura

`casos/` (casos de teste em JSON + `respostas/` gravadas) e `dados/` (tabelas) são a fonte; `r/` e `python/`
têm cópias. Mudou `casos/`, `dados/` ou o `README.md`: `python ferramentas/sincronizar.py` (um teste acusa
cópia esquecida). `ferramentas/gerar_tabelas.py` refaz `dados/` pela Wikipédia.

Testar:
- Python: `cd python && uv run pytest && uv run ruff check src tests ../ferramentas`
- R: `R CMD build r` e `R CMD check --as-cran --no-manual veiculosbr_*.tar.gz` (sem LaTeX nesta máquina);
  antes, `roxygen2::roxygenise()` dentro de `r/` se mudou documentação ou export.

## Regras

- **Responder em português (PT-BR).** Código, nomes de função e documentação também em português.
- **Escrever como o usuário escreve** (pedido dele): nomes descritivos, nada de `x`, `df`, `tmp`, `i`; no R,
  `=` para atribuir, R base, passo a passo com `if`/`else`; no Python, funções curtas, constantes com nome.
  Comentário só para o "porquê".
- **Nada da empresa entra aqui.** O usuário trabalha num grupo de revendas, e o código de lá (Control,
  revendas, CNPJs, placas da frota, regras internas) não pode ser copiado. Tudo é escrito do zero, de forma
  genérica. Placa real nos testes só a de exemplo da documentação pública (ABC1D23); as inventadas começam
  com ZZ (faixa que nenhum estado recebeu).
- **R e Python dão a mesma resposta.** Mesmos nomes de função, mesmos casos em `casos/*.json`. Ordenação de
  texto no R com `order(..., method = "radix")`, para bater com o Python.
- **Toda documentação diz de onde vem o dado** (pedido do usuário): a seção "De onde vêm os dados" do README
  e do `?veiculosbr`, `@source` nas funções, `fonte`/`origem` em todo resultado que vem da internet, e
  `dados/LEIAME.md` para as tabelas. Fonte nova = linha nova nas três.
- **Fonte de dados só se permitir.** Respeitar o `robots.txt` e nunca contornar Cloudflare, captcha ou
  bloqueio, nem com navegador sem tela, nem procurando API escondida no JavaScript do site. A lista de fontes
  aceitas e recusadas fica em `docs/plano.md`.
- **FIPE pela placa pode estar errada, e o pacote diz isso.** Todo resultado traz a fonte, a confiança e
  TODOS os candidatos de FIPE quando houver mais de um, nunca só o "melhor".
- **Não gastar cota nem paciência dos sites.** A busca por placa do Parallelum dá 5 consultas por mês sem
  token (a de outubro/2026 já foi gasta em 26/10): nunca usar em teste nem em experimento sem o usuário
  pedir. O tabelafipebrasil.com limita por IP: desenvolver com as respostas gravadas e consultar ao vivo no
  máximo uma vez para conferir. Para gravar respostas novas do catálogo (que é folgado, 1.000/dia):
  `VEICULOSBR_CACHE=0 VEICULOSBR_GRAVAR_RESPOSTAS=<caminho>/casos/respostas`.
- **CRAN:** strings do código R só em ASCII, com `\u00e3` no lugar do acento (comentário e roxygen podem
  ter acento). Cuidado: a ferramenta de escrita de arquivo transforma `\u00e3` na própria letra; depois de
  escrever um `.R`, conferir com `R CMD check` (ou `tools::showNonASCIIfile`). Caminho de arquivo dentro do
  pacote R com até 100 caracteres: por isso os nomes gravados usam apelido do site (`parallelum_...`).
- **`Rscript -e` com várias linhas no Git Bash pode derrubar o R** (segmentation fault sem mensagem): rodar
  R por arquivo `.R`.
- **Sem emoji em arquivo-fonte**, nem em comentário.
