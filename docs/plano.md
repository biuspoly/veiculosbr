# Plano do veiculosbr

Situação em 26/10/2026: só o plano. Nenhum código ainda, as dependências esperam a aprovação do usuário.

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
   - a placa vai à busca por placa do Parallelum, que devolve o veículo (marca, modelo, ano, combustível,
     cidade) e a lista `fipePrices`. Quando há mais de um preço, todos voltam;
   - quando a lista vem vazia (acontece: o exemplo da própria documentação volta sem preço), o pacote
     procura no catálogo os modelos daquela marca e ano parecidos com o nome do modelo e devolve **todos
     os candidatos**, cada um com uma nota de semelhança;
   - todo resultado diz a fonte, o grau de confiança e o aviso de que pode estar errado.

## Dependências

### R

| Pacote | Tipo | Para quê |
|---|---|---|
| (nenhum) | — | placa, RENAVAM e chassi: só R base |
| `httr2` | obrigatória | chamadas ao Parallelum, com nova tentativa, limite de ritmo e cache |
| `jsonlite` | obrigatória | ler a resposta da API |
| `testthat` | teste | a suíte de testes |
| `httptest2` | teste | grava a resposta da API uma vez; os testes leem o arquivo e não gastam cota |

A semelhança entre nomes de modelo usa `adist()`, do próprio R, sem `stringdist`.

### Python

| Pacote | Tipo | Para quê |
|---|---|---|
| (nenhum) | — | placa, RENAVAM e chassi: só a biblioteca padrão |
| `httpx` | obrigatória | chamadas ao Parallelum, com prazo de resposta e repetição |
| `platformdirs` | obrigatória | a pasta de cache certa em Windows, Mac e Linux (pequena, sem compilação) |
| `pytest` | teste | a suíte de testes |
| `respx` | teste | o equivalente do `httptest2` para o `httpx` |
| `uv`, `ruff` | ferramenta | ambiente, empacotamento e padrão de código |

A semelhança usa o mesmo algoritmo escrito nas duas linguagens (distância de Levenshtein sobre o nome
normalizado), sem `rapidfuzz`, para que a nota saia idêntica em R e em Python.

### O que fica de fora

- **Raspar sites de placa.** O placafipe.com proíbe robôs nas páginas de placa e as protege com Cloudflare.
  Outra fonte só entra se permitir, como um adaptador à parte, ou por uma API paga com a chave do usuário.
- **Dono, débitos e multas.** São dados pessoais (LGPD), e os serviços do Detran pedem login e captcha.

## Ordem

1. `casos/*.json`, placa e RENAVAM nas duas linguagens (sem internet).
2. Chassi.
3. FIPE pelo catálogo, com o cache.
4. FIPE pela placa e os candidatos.
5. Publicar: o repositório aberto e o r-universe primeiro, depois o PyPI; o CRAN por último, porque tem
   revisão humana.
