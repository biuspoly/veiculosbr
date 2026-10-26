# Plano do veiculosbr

Situação em 26/10/2026: só o plano, sem código. Nome e dependências aprovados pelo usuário. Sem token
nem plano pago do Parallelum (decisão dele): a busca por placa vive das fontes abertas abaixo.

## O que já existe

| Peça | Python | R |
|---|---|---|
| Placa: validar, formatar, converter para Mercosul | `brutils` (MIT) | nada |
| RENAVAM | `brutils` (`is_valid_renavam`) | nada |
| Chassi (VIN) | nada voltado ao Brasil | nada |
| Tabela FIPE | `pyfipe` (lê o site da FIPE, devolve pandas); `python-fipe` arquivado em 2018 | `fipe` (Italo Cegatta) saiu do CRAN em 24/04/2022 por erro não corrigido |
| FIPE pela placa | nada | nada |

No R o espaço está vazio. No Python, o `veiculosbr` só se justifica fazendo mais que o `brutils` e o `pyfipe`.

## O que o pacote faz

1. **Placa.** Valida, formata e diz o tipo (antiga ou Mercosul). Converte nos dois sentidos, avisando que
   uma placa que já nasceu Mercosul nunca teve versão antiga. Indica o estado provável pela faixa de letras
   da placa antiga (tabela pública, a conferir antes de entrar).
2. **RENAVAM.** Confere o dígito (módulo 11) e aceita o número antigo de 9 dígitos, completando com zeros.
3. **Chassi.** Confere a estrutura (17 caracteres, sem I, O e Q) e diz o fabricante (os 3 primeiros
   caracteres) e o ano-modelo (o 10º caractere). Esse caractere se repete a cada 30 anos, então volta com
   as duas possibilidades.
4. **FIPE pelo catálogo.** Marcas, modelos, anos, preço e código FIPE, pela API do Parallelum (v2), com
   cache local.
5. **FIPE pela placa**, em cascata:
   - a placa vai às fontes de placa (abaixo), que devolvem o veículo (marca, modelo, ano, combustível,
     cidade) e, às vezes, os preços FIPE. Quando há mais de um preço, todos voltam;
   - quando nenhuma traz preço (acontece: o exemplo da documentação volta sem preço nas duas), o pacote
     procura no catálogo os modelos daquela marca e ano parecidos com o nome do modelo e devolve **todos
     os candidatos**, cada um com uma nota de semelhança;
   - todo resultado diz a fonte, o grau de confiança e o aviso de que pode estar errado.

## Fontes de placa

Conferidas em 26/10/2026, sempre com a placa de exemplo da documentação (ABC1D23):

| Fonte | Robôs | Como responde | Decisão |
|---|---|---|---|
| Parallelum, `/api/v2/plates/{placa}` | API pública | JSON; 5 consultas/mês sem token | **fonte 1** (cota pequena, mas é API) |
| tabelafipebrasil.com, `/placa/{placa}` | permitidos | HTML simples, sem desafio, mesmo com o robô se identificando; a API própria deles está desligada | **fonte 2**, lida com `rvest` / `selectolax` |
| placafipe.com.br | permitidos | aplicativo que só monta a página com JavaScript | **fonte 3, opcional**, por navegador sem tela (`chromote` / `pydoll`); a testar |
| placafipe.com | bloqueia `/placa/` para robôs de IA; Cloudflare 403 | — | fora |
| keplaca.com | o mesmo `robots.txt` do placafipe.com; desafio do Cloudflare | — | fora |
| consultarplaca.com.br | — | pago por crédito | fora (só pela chave do usuário, se um dia ele quiser) |

As fontes 1 e 2 devolveram o mesmo veículo (mesmo final de chassi), sinal de que leem a mesma base.

Regras de toda fonte raspada: o robô se identifica (`veiculosbr/<versão>` + link do repositório), no
máximo 1 consulta por segundo, cache local de 30 dias por placa, e ela para de ser consultada quando o
`robots.txt` mudar para proibir, conferido a cada sessão. Um site que muda o desenho quebra só aquela
fonte: as outras seguem, e o resultado diz qual falhou.

`chromote` e `pydoll` falam com o Chrome pelo mesmo protocolo (DevTools), sem Selenium. Entram só para
montar páginas de sites que permitem robôs. O recurso do `pydoll` de passar pelo Cloudflare **não** é
usado: um site com desafio está dizendo que não quer robô.

## Dependências

### R

| Pacote | Tipo | Para quê |
|---|---|---|
| (nenhum) | — | placa, RENAVAM e chassi: só R base |
| `httr2` | obrigatória | chamadas ao Parallelum, com nova tentativa, limite de ritmo e cache |
| `jsonlite` | obrigatória | ler a resposta da API |
| `rvest` | obrigatória | ler a página de placa do tabelafipebrasil |
| `chromote` | opcional (Suggests) | a fonte 3, que só existe com JavaScript; pede o Chrome instalado |
| `testthat` | teste | a suíte de testes |
| `httptest2` | teste | grava a resposta da API uma vez; os testes leem o arquivo e não gastam cota |

A semelhança entre nomes de modelo usa `adist()`, do próprio R, sem `stringdist`.

### Python

| Pacote | Tipo | Para quê |
|---|---|---|
| (nenhum) | — | placa, RENAVAM e chassi: só a biblioteca padrão |
| `httpx` | obrigatória | chamadas ao Parallelum, com prazo de resposta e repetição |
| `platformdirs` | obrigatória | a pasta de cache certa em Windows, Mac e Linux (pequena, sem compilação) |
| `selectolax` | obrigatória | ler a página de placa do tabelafipebrasil (rápido, com instalador pronto para os três sistemas) |
| `pydoll-python` | opcional (`veiculosbr[navegador]`) | a fonte 3; o mesmo papel do `chromote` |
| `pytest` | teste | a suíte de testes |
| `respx` | teste | o equivalente do `httptest2` para o `httpx` |
| `uv`, `ruff` | ferramenta | ambiente, empacotamento e padrão de código |

A semelhança usa o mesmo algoritmo escrito nas duas linguagens (distância de Levenshtein sobre o nome
normalizado), sem `rapidfuzz`, para que a nota saia idêntica em R e em Python.

### O que fica de fora

- **Sites que bloqueiam robôs** (placafipe.com, keplaca.com): nem por navegador sem tela.
- **Dono, débitos e multas.** São dados pessoais (LGPD), e os serviços do Detran pedem login e captcha.

## Ordem

1. `casos/*.json`, placa e RENAVAM nas duas linguagens (sem internet).
2. Chassi.
3. FIPE pelo catálogo, com o cache.
4. FIPE pela placa e os candidatos.
5. Publicar: o repositório aberto e o r-universe primeiro, depois o PyPI; o CRAN por último, porque tem
   revisão humana.
