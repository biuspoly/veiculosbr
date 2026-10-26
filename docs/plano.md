# Plano do veiculosbr

Situação em 26/10/2026: **versão 0.1.0 pronta nas duas linguagens.** Enxugada no mesmo dia, a pedido do
usuário: sem chassi, sem conferência de `robots.txt`, sem cache em disco ("é consulta, não quero salvar
nada") e só 13 funções públicas. O R passa no `R CMD check --as-cran`
sem erro, aviso ou nota; o Python passa no pytest e no ruff. Os dois conferem os mesmos casos de `casos/`.
Ainda não publicado (repositório privado).

## O que já existia antes

| Peça | Python | R |
|---|---|---|
| Placa: validar, formatar, converter para Mercosul | `brutils` (MIT) | nada |
| RENAVAM | `brutils` (`is_valid_renavam`) | nada |
| Tabela FIPE | `pyfipe` (lê o site da FIPE, devolve pandas); `python-fipe` arquivado em 2018 | `fipe` (Italo Cegatta) saiu do CRAN em 24/04/2022 |
| FIPE pela placa | nada | nada |

O que o veiculosbr faz a mais que o `brutils`: converte a placa nos dois sentidos, diz o estado de origem pela
faixa de letras e tem o FIPE pela placa com todos os candidatos.
O RENAVAM foi conferido contra o `brutils` em 20.000 números aleatórios, sem nenhuma diferença.

## O que o pacote faz (as 13 funções públicas)

1. **Placa**: `placa_valida`, `placa_tipo`, `placa_para_mercosul`, `placa_para_antiga`, `placa_formatar`,
   `placa_uf`.
2. **RENAVAM**: `renavam_valido` (aceita o antigo, de 9 dígitos).
3. **FIPE pelo catálogo**: `fipe_marcas`, `fipe_modelos`, `fipe_anos`, `fipe_preco`, pela API v2 do Parallelum.
4. **FIPE pela placa**: `fipe_por_placa` (a cascata) e `fipe_candidatos` (a busca por nome parecido):
   - os códigos que a fonte da placa mostra são conferidos no catálogo, no ano-modelo do veículo;
   - sem código na fonte, entram todos os modelos da marca naquele ano a até 0,15 da nota do melhor (piso
     0,3). Uma nota mínima fixa não servia: o cadastro escreve "15.190 CRM 4X2 4P" e a FIPE "15-190 E
     Worker 2p", e o certo fica com 0,36;
   - sem ano-modelo, procura nos dois anos possíveis; sem tipo de veículo, escolhe pelo catálogo;
   - reboque e o que mais a FIPE não cobre voltam sem candidato e com o aviso.

Conferido em 26/10/2026 com quatro placas reais (que não entram no repositório): só pelo catálogo, o pacote
achou os mesmos códigos e preços que o tabelafipebrasil mostrava.

## Fontes de placa

| Fonte | Robôs | Como responde | Decisão |
|---|---|---|---|
| tabelafipebrasil.com, `/placa/{placa}` | permitidos | HTML simples; **limita as consultas por IP** (429 do Cloudflare depois de pouco mais de uma dezena numa tarde, por mais de uma hora) | **fonte padrão**, devagar e com cache |
| Parallelum, `/api/v2/plates/{placa}` | API pública | JSON; 5 consultas/**mês** sem token, 10 com o token gratuito | **só quando pedida**; o pacote avisa quantas sobraram |
| placafipe.com.br | permitidos | aplicativo que só monta a página com JavaScript | **fora por enquanto**: o chromote não abriu o navegador nesta máquina (sem Chrome; o Edge sem tela não subiu), e código não testado não entra |
| placafipe.com | bloqueia `/placa/` para robôs de IA; Cloudflare 403 | — | fora |
| keplaca.com | o mesmo `robots.txt` do placafipe.com; desafio do Cloudflare | — | fora |
| consultarplaca.com.br | — | pago por crédito | fora |

O tabelafipebrasil e o Parallelum devolveram o mesmo veículo (mesmo final de chassi): leem a mesma base.

Regras de toda fonte lida: o robô se identifica, espera 3 s entre consultas ao mesmo site e fica 10 minutos
sem consultar um site que respondeu 429 ou 403. Nada vai para o disco; a mesma consulta na mesma sessão sai
da memória. O recurso do `pydoll` de passar pelo Cloudflare **não** é usado: um site com desafio
está dizendo que não quer robô.

## Dependências

| | R | Python |
|---|---|---|
| Placa e RENAVAM | R base | biblioteca padrão |
| Rede | `httr2`, `jsonlite` | `httpx` |
| Página de placa | `rvest` | `selectolax` (leitor `lexbor`; o antigo saiu na 1.0) |
| Testes | `testthat`, `withr` | `pytest` |

A semelhança usa a mesma conta nas duas linguagens (Levenshtein: `adist` no R, escrita à mão no Python), sem
`stringdist` nem `rapidfuzz`. Os testes não usam `httptest2` nem `respx`, como estava no plano: as duas
linguagens leem as respostas gravadas da mesma pasta (`VEICULOSBR_RESPOSTAS_GRAVADAS`), com o mesmo nome de
arquivo, o que dispensa uma dependência de cada lado. `chromote` e `pydoll` ficaram de fora com a fonte do
placafipe.com.br.

## Próximos passos

1. Tornar o repositório público e publicar: r-universe e PyPI primeiro; CRAN depois (tem revisão humana).
2. Uma página de demonstração no site de portfólio (`biuspoly/portfolio`).
3. Testar o placafipe.com.br numa máquina com o Chrome instalado; se funcionar, entra como fonte opcional.
4. Refazer `dados/` quando o Senatran distribuir faixas novas (a tabela é a de janeiro de 2025).

## O que saiu, e por quê

- **Chassi** (país, fabricante, ano-modelo, dígito 9): o usuário não quis. As duas tabelas da Wikipédia saíram
  junto.
- **Conferência do `robots.txt`**: o usuário achou desnecessária. A escolha das fontes continua: site que se
  protege com desafio anti-robô não é usado.
- **Cache em disco** (7 dias o catálogo, 30 a placa): "é consulta, não quero salvar nada". Ficou só a memória
  da sessão, que evita repetir a mesma consulta dentro de uma busca (a lista de marcas é pedida várias vezes).
- **Funções que só serviam de peça** (limpar placa e RENAVAM, dígito do RENAVAM, valor em reais, os endpoints
  miúdos do catálogo, a nota de semelhança e `placa_consultar`) continuam por dentro, fora da lista pública.
